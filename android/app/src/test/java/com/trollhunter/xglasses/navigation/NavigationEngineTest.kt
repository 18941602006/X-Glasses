package com.trollhunter.xglasses.navigation

import org.junit.Assert.assertEquals
import org.junit.Assert.assertThrows
import org.junit.Assert.assertTrue
import org.junit.Test

class NavigationEngineTest {
    private val destination = PlaceCandidate("dest", "测试终点", GeoPoint(30.0004, 120.0))
    private val route = WalkingRoute(
        id = "route-1",
        providerId = "test",
        destination = destination,
        steps = listOf(
            RouteStep("向前直行", Maneuver.STRAIGHT, GeoPoint(30.0002, 120.0), 22),
            RouteStep("到达终点附近", Maneuver.ARRIVE, destination.point, 22),
        ),
        geometry = listOf(GeoPoint(30.0, 120.0), GeoPoint(30.0002, 120.0), destination.point),
        totalDistanceM = 44,
    )

    @Test
    fun advancesStepAndArrivesNearDestination() {
        val engine = NavigationEngine()
        engine.start(route, 1_000)
        val advanced = engine.update(LocationFix(GeoPoint(30.0002, 120.0), 3f, 2_000), 2_000)
        assertEquals(Maneuver.ARRIVE, advanced.maneuver)
        val arrived = engine.update(LocationFix(GeoPoint(30.00039, 120.0), 3f, 3_000), 3_000)
        assertEquals(GuidanceStatus.ARRIVED, arrived.status)
        assertEquals(0, arrived.remainingDistanceM)
    }

    @Test
    fun staleOrInaccurateLocationPausesGuidance() {
        val engine = NavigationEngine()
        engine.start(route, 1_000)
        val stale = engine.update(LocationFix(GeoPoint(30.0, 120.0), 3f, 1_000), 20_000)
        assertEquals(GuidanceStatus.PAUSED, stale.status)
        assertEquals("location_unusable", stale.reason)
    }

    @Test
    fun repeatedOffRouteFixesRequestReroute() {
        val engine = NavigationEngine()
        engine.start(route, 1_000)
        var result = engine.snapshot
        repeat(3) { index ->
            result = engine.update(LocationFix(GeoPoint(30.0, 120.002), 3f, 2_000L + index), 2_000L + index)
        }
        assertEquals(GuidanceStatus.REROUTE_REQUIRED, result.status)
        assertTrue(result.instruction.contains("重新规划"))
    }

    @Test
    fun routingAndFailureNeverClaimSafeMovement() {
        val engine = NavigationEngine()
        engine.routing(destination, 1_000)
        assertEquals(GuidanceStatus.ROUTING, engine.snapshot.status)
        val failed = engine.fail("offline", 2_000)
        assertEquals(GuidanceStatus.FAILED, failed.status)
        assertTrue(failed.instruction.contains("停下"))
    }

    @Test
    fun providerConfigurationRequiresHttps() {
        assertThrows(IllegalArgumentException::class.java) {
            NavigationProviderConfig("http" + "://geocoder.example", "https" + "://router.example")
        }
    }

    @Test
    fun polyline6DecoderKeepsCoordinateOrder() {
        val points = decodePolyline6("??AA")
        assertEquals(GeoPoint(0.0, 0.0), points[0])
        assertEquals(GeoPoint(0.000001, 0.000001), points[1])
    }
}
