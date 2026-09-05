package com.trollhunter.xglasses.navigation

import kotlin.math.abs

data class GeoPoint(val latitude: Double, val longitude: Double) {
    init {
        require(latitude.isFinite() && latitude in -90.0..90.0) { "invalid latitude" }
        require(longitude.isFinite() && longitude in -180.0..180.0) { "invalid longitude" }
    }
}

data class PlaceCandidate(
    val id: String,
    val label: String,
    val point: GeoPoint,
) {
    init {
        require(id.isNotBlank() && id.length <= 160) { "invalid place id" }
        require(label.isNotBlank() && label.length <= 240) { "invalid place label" }
    }
}

enum class Maneuver { STRAIGHT, LEFT, RIGHT, ARRIVE, UNKNOWN }

data class RouteStep(
    val instruction: String,
    val maneuver: Maneuver,
    val target: GeoPoint,
    val distanceM: Int,
) {
    init {
        require(instruction.isNotBlank() && instruction.length <= 300) { "invalid instruction" }
        require(distanceM in 0..100_000) { "invalid step distance" }
    }
}

data class WalkingRoute(
    val id: String,
    val providerId: String,
    val destination: PlaceCandidate,
    val steps: List<RouteStep>,
    val geometry: List<GeoPoint>,
    val totalDistanceM: Int,
) {
    init {
        require(id.isNotBlank() && id.length <= 160) { "invalid route id" }
        require(providerId.isNotBlank() && providerId.length <= 120) { "invalid provider" }
        require(steps.isNotEmpty() && steps.size <= 512) { "invalid route steps" }
        require(geometry.size in 2..20_000) { "invalid route geometry" }
        require(totalDistanceM in 1..1_000_000) { "invalid route distance" }
    }
}

data class LocationFix(
    val point: GeoPoint,
    val accuracyM: Float,
    val elapsedRealtimeMs: Long,
) {
    init {
        require(accuracyM.isFinite() && accuracyM >= 0f) { "invalid location accuracy" }
        require(elapsedRealtimeMs >= 0) { "invalid location time" }
    }
}

enum class GuidanceStatus { IDLE, ROUTING, ACTIVE, PAUSED, REROUTE_REQUIRED, ARRIVED, FAILED }

data class GuidanceSnapshot(
    val status: GuidanceStatus = GuidanceStatus.IDLE,
    val destinationLabel: String? = null,
    val routeId: String? = null,
    val instruction: String = "尚未开始导航",
    val maneuver: Maneuver = Maneuver.UNKNOWN,
    val distanceToStepM: Int? = null,
    val remainingDistanceM: Int? = null,
    val reason: String? = null,
    val updatedElapsedRealtimeMs: Long? = null,
)

data class NavigationUiState(
    val providerConfigured: Boolean = false,
    val providerName: String = "未配置",
    val privacyConsentRequired: Boolean = false,
    val privacyConsentGranted: Boolean = false,
    val locationPermissionGranted: Boolean = false,
    val query: String = "",
    val searching: Boolean = false,
    val routeLoading: Boolean = false,
    val candidates: List<PlaceCandidate> = emptyList(),
    val selected: PlaceCandidate? = null,
    val guidance: GuidanceSnapshot = GuidanceSnapshot(),
    val error: String? = null,
)

fun LocationFix.isUsable(nowElapsedRealtimeMs: Long, maximumAgeMs: Long, maximumAccuracyM: Float): Boolean =
    nowElapsedRealtimeMs >= elapsedRealtimeMs &&
        nowElapsedRealtimeMs - elapsedRealtimeMs <= maximumAgeMs &&
        accuracyM <= maximumAccuracyM &&
        abs(point.latitude) <= 90.0
