package com.trollhunter.xglasses.navigation

import android.content.Context
import com.amap.api.maps.CoordinateConverter
import com.amap.api.maps.model.LatLng
import com.amap.api.services.core.AMapException
import com.amap.api.services.core.LatLonPoint
import com.amap.api.services.core.PoiItem
import com.amap.api.services.poisearch.PoiResult
import com.amap.api.services.poisearch.PoiSearch
import com.amap.api.services.route.BusRouteResult
import com.amap.api.services.route.DriveRouteResult
import com.amap.api.services.route.RideRouteResult
import com.amap.api.services.route.RouteSearch
import com.amap.api.services.route.WalkRouteResult
import java.util.concurrent.CountDownLatch
import java.util.concurrent.TimeUnit
import java.util.concurrent.atomic.AtomicReference

class AmapNavigationProvider(private val context: Context) : NavigationProvider {
    override val providerId = "amap-android"
    override val displayName = "高德地图"

    override fun normalizeLocation(point: GeoPoint): GeoPoint {
        val converted = CoordinateConverter(context)
            .from(CoordinateConverter.CoordType.GPS)
            .coord(LatLng(point.latitude, point.longitude))
            .convert()
        return GeoPoint(converted.latitude, converted.longitude)
    }

    override fun search(query: String, near: GeoPoint?): List<PlaceCandidate> {
        require(query == query.trim() && query.length in 2..120) { "invalid destination query" }
        val searchQuery = PoiSearch.Query(query, "", "").apply {
            pageSize = 5
            pageNum = 1
        }
        val search = PoiSearch(context, searchQuery)
        val response = AtomicReference<PoiResult?>()
        val failureCode = AtomicReference<Int?>()
        val latch = CountDownLatch(1)
        search.setOnPoiSearchListener(object : PoiSearch.OnPoiSearchListener {
            override fun onPoiSearched(result: PoiResult?, code: Int) {
                response.set(result)
                failureCode.set(code)
                latch.countDown()
            }

            override fun onPoiItemSearched(item: PoiItem?, code: Int) = Unit
        })
        search.searchPOIAsyn()
        require(latch.await(8, TimeUnit.SECONDS)) { "amap search timeout" }
        require(failureCode.get() == AMapException.CODE_AMAP_SUCCESS) {
            "amap search failure ${failureCode.get()}"
        }
        return response.get()?.pois.orEmpty().take(5).mapNotNull { item ->
            val location = item.latLonPoint ?: return@mapNotNull null
            val label = listOfNotNull(item.title, item.snippet)
                .filter { it.isNotBlank() }
                .distinct()
                .joinToString("，")
                .take(240)
            if (label.isBlank()) return@mapNotNull null
            PlaceCandidate(
                id = item.poiId?.takeIf { it.isNotBlank() } ?: "amap-${label.hashCode().toUInt().toString(16)}",
                label = label,
                point = location.toGeoPoint(),
            )
        }
    }

    override fun walkingRoute(origin: GeoPoint, destination: PlaceCandidate): WalkingRoute {
        val routeSearch = RouteSearch(context)
        val response = AtomicReference<WalkRouteResult?>()
        val failureCode = AtomicReference<Int?>()
        val latch = CountDownLatch(1)
        routeSearch.setRouteSearchListener(object : RouteSearch.OnRouteSearchListener {
            override fun onBusRouteSearched(result: BusRouteResult?, code: Int) = Unit
            override fun onDriveRouteSearched(result: DriveRouteResult?, code: Int) = Unit
            override fun onRideRouteSearched(result: RideRouteResult?, code: Int) = Unit

            override fun onWalkRouteSearched(result: WalkRouteResult?, code: Int) {
                response.set(result)
                failureCode.set(code)
                latch.countDown()
            }
        })
        val endpoints = RouteSearch.FromAndTo(origin.toLatLonPoint(), destination.point.toLatLonPoint())
        routeSearch.calculateWalkRouteAsyn(RouteSearch.WalkRouteQuery(endpoints, RouteSearch.WALK_DEFAULT))
        require(latch.await(10, TimeUnit.SECONDS)) { "amap route timeout" }
        require(failureCode.get() == AMapException.CODE_AMAP_SUCCESS) {
            "amap route failure ${failureCode.get()}"
        }
        val path = response.get()?.paths?.firstOrNull() ?: error("amap route has no walking path")
        val geometry = path.steps.orEmpty()
            .flatMap { it.polyline.orEmpty() }
            .map { it.toGeoPoint() }
            .deduplicateAdjacent()
        require(geometry.size >= 2) { "amap route shape too short" }
        val steps = path.steps.orEmpty().mapNotNull { step ->
            val target = step.polyline?.lastOrNull()?.toGeoPoint() ?: return@mapNotNull null
            val instruction = step.instruction?.takeIf { it.isNotBlank() } ?: "继续沿步行路线前进"
            RouteStep(
                instruction = instruction.take(300),
                maneuver = amapManeuver(step.action, instruction),
                target = target,
                distanceM = step.distance.toInt().coerceIn(0, 100_000),
            )
        }
        require(steps.isNotEmpty()) { "amap route has no walking steps" }
        return WalkingRoute(
            id = "amap-${destination.id}-${geometry.hashCode().toUInt().toString(16)}".take(160),
            providerId = providerId,
            destination = destination,
            steps = steps,
            geometry = geometry,
            totalDistanceM = path.distance.toInt().coerceIn(1, 1_000_000),
        )
    }
}

internal fun amapManeuver(action: String?, instruction: String): Maneuver {
    val text = listOfNotNull(action, instruction).joinToString(" ")
    return when {
        "到达" in text || "终点" in text -> Maneuver.ARRIVE
        "左转" in text || "向左" in text -> Maneuver.LEFT
        "右转" in text || "向右" in text -> Maneuver.RIGHT
        text.isNotBlank() -> Maneuver.STRAIGHT
        else -> Maneuver.UNKNOWN
    }
}

private fun GeoPoint.toLatLonPoint() = LatLonPoint(latitude, longitude)
private fun LatLonPoint.toGeoPoint() = GeoPoint(latitude, longitude)

private fun List<GeoPoint>.deduplicateAdjacent(): List<GeoPoint> =
    fold(mutableListOf()) { result, point ->
        if (result.lastOrNull() != point) result += point
        result
    }
