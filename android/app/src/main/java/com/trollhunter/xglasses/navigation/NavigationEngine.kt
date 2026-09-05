package com.trollhunter.xglasses.navigation

import kotlin.math.PI
import kotlin.math.asin
import kotlin.math.cos
import kotlin.math.max
import kotlin.math.min
import kotlin.math.roundToInt
import kotlin.math.sin
import kotlin.math.sqrt

data class NavigationConfig(
    val maximumFixAgeMs: Long = 10_000,
    val maximumAccuracyM: Float = 50f,
    val stepReachedM: Double = 14.0,
    val arrivalM: Double = 18.0,
    val offRouteM: Double = 45.0,
    val offRouteConfirmations: Int = 3,
) {
    init {
        require(maximumFixAgeMs in 1_000..60_000)
        require(maximumAccuracyM in 5f..100f)
        require(stepReachedM in 3.0..50.0)
        require(arrivalM in 3.0..60.0)
        require(offRouteM in 15.0..200.0)
        require(offRouteConfirmations in 2..10)
    }
}
class NavigationEngine(private val config: NavigationConfig = NavigationConfig()) {
    private var route: WalkingRoute? = null
    private var stepIndex = 0
    private var offRouteCount = 0
    var snapshot: GuidanceSnapshot = GuidanceSnapshot()
        private set

    fun routing(destination: PlaceCandidate, nowMs: Long) {
        route = null
        stepIndex = 0
        offRouteCount = 0
        snapshot = GuidanceSnapshot(
            status = GuidanceStatus.ROUTING,
            destinationLabel = destination.label,
            instruction = "正在规划步行路线",
            updatedElapsedRealtimeMs = nowMs,
        )
    }

    fun start(newRoute: WalkingRoute, nowMs: Long): GuidanceSnapshot {
        route = newRoute
        stepIndex = 0
        offRouteCount = 0
        val step = newRoute.steps.first()
        snapshot = GuidanceSnapshot(
            status = GuidanceStatus.ACTIVE,
            destinationLabel = newRoute.destination.label,
            routeId = newRoute.id,
            instruction = step.instruction,
            maneuver = step.maneuver,
            remainingDistanceM = newRoute.totalDistanceM,
            updatedElapsedRealtimeMs = nowMs,
        )
        return snapshot
    }

    fun update(fix: LocationFix, nowMs: Long): GuidanceSnapshot {
        val activeRoute = route ?: return snapshot
        if (!fix.isUsable(nowMs, config.maximumFixAgeMs, config.maximumAccuracyM)) {
            snapshot = snapshot.copy(
                status = GuidanceStatus.PAUSED,
                instruction = "定位精度不足，地图指引已暂停，请停下确认环境",
                maneuver = Maneuver.UNKNOWN,
                reason = "location_unusable",
                updatedElapsedRealtimeMs = nowMs,
            )
            return snapshot
        }

        val destinationDistance = distanceM(fix.point, activeRoute.destination.point)
        if (destinationDistance <= config.arrivalM) {
            snapshot = snapshot.copy(
                status = GuidanceStatus.ARRIVED,
                instruction = "已到达目的地附近，请结合现场环境确认具体入口",
                maneuver = Maneuver.ARRIVE,
                distanceToStepM = destinationDistance.roundToInt(),
                remainingDistanceM = 0,
                reason = null,
                updatedElapsedRealtimeMs = nowMs,
            )
            return snapshot
        }

        val deviation = distanceToPolylineM(fix.point, activeRoute.geometry)
        offRouteCount = if (deviation > config.offRouteM) offRouteCount + 1 else 0
        if (offRouteCount >= config.offRouteConfirmations) {
            snapshot = snapshot.copy(
                status = GuidanceStatus.REROUTE_REQUIRED,
                instruction = "检测到可能偏离路线，正在重新规划；请停下确认环境",
                maneuver = Maneuver.UNKNOWN,
                reason = "off_route",
                updatedElapsedRealtimeMs = nowMs,
            )
            return snapshot
        }

        while (stepIndex < activeRoute.steps.lastIndex &&
            distanceM(fix.point, activeRoute.steps[stepIndex].target) <= config.stepReachedM
        ) {
            stepIndex += 1
        }
        val step = activeRoute.steps[stepIndex]
        val stepDistance = distanceM(fix.point, step.target).roundToInt().coerceAtLeast(0)
        val remaining = (stepDistance + activeRoute.steps.drop(stepIndex + 1).sumOf { it.distanceM })
            .coerceAtMost(activeRoute.totalDistanceM)
        snapshot = GuidanceSnapshot(
            status = GuidanceStatus.ACTIVE,
            destinationLabel = activeRoute.destination.label,
            routeId = activeRoute.id,
            instruction = step.instruction,
            maneuver = step.maneuver,
            distanceToStepM = stepDistance,
            remainingDistanceM = remaining,
            reason = null,
            updatedElapsedRealtimeMs = nowMs,
        )
        return snapshot
    }

    fun fail(reason: String, nowMs: Long): GuidanceSnapshot {
        route = null
        snapshot = snapshot.copy(
            status = GuidanceStatus.FAILED,
            instruction = "地图导航不可用，请停下并使用其他方式确认路线",
            maneuver = Maneuver.UNKNOWN,
            reason = reason.take(120),
            updatedElapsedRealtimeMs = nowMs,
        )
        return snapshot
    }

    fun stop(): GuidanceSnapshot {
        route = null
        stepIndex = 0
        offRouteCount = 0
        snapshot = GuidanceSnapshot()
        return snapshot
    }
}

internal fun distanceM(a: GeoPoint, b: GeoPoint): Double {
    val radius = 6_371_000.0
    val lat1 = a.latitude * PI / 180.0
    val lat2 = b.latitude * PI / 180.0
    val dLat = (b.latitude - a.latitude) * PI / 180.0
    val dLon = (b.longitude - a.longitude) * PI / 180.0
    val h = sin(dLat / 2) * sin(dLat / 2) + cos(lat1) * cos(lat2) * sin(dLon / 2) * sin(dLon / 2)
    return radius * 2 * asin(min(1.0, sqrt(h)))
}

private fun distanceToPolylineM(point: GeoPoint, geometry: List<GeoPoint>): Double {
    val referenceLat = point.latitude * PI / 180.0
    fun xy(value: GeoPoint): Pair<Double, Double> {
        val x = (value.longitude - point.longitude) * PI / 180.0 * 6_371_000.0 * cos(referenceLat)
        val y = (value.latitude - point.latitude) * PI / 180.0 * 6_371_000.0
        return x to y
    }
    return geometry.zipWithNext().minOf { (start, end) ->
        val (ax, ay) = xy(start)
        val (bx, by) = xy(end)
        val dx = bx - ax
        val dy = by - ay
        val denominator = dx * dx + dy * dy
        val t = if (denominator == 0.0) 0.0 else max(0.0, min(1.0, -(ax * dx + ay * dy) / denominator))
        val closestX = ax + t * dx
        val closestY = ay + t * dy
        sqrt(closestX * closestX + closestY * closestY)
    }
}
