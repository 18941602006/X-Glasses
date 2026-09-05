package com.trollhunter.xglasses.navigation

import org.junit.Assert.assertEquals
import org.junit.Test

class AmapNavigationProviderTest {
    @Test
    fun mapsChineseTurnActionsWithoutGrantingPassage() {
        assertEquals(Maneuver.LEFT, amapManeuver("左转", "向左转进入道路"))
        assertEquals(Maneuver.RIGHT, amapManeuver("右转", "向右转"))
        assertEquals(Maneuver.STRAIGHT, amapManeuver("直行", "继续前进"))
    }

    @Test
    fun arrivalActionIsReportedAsArrivalOnly() {
        assertEquals(Maneuver.ARRIVE, amapManeuver("", "到达终点附近"))
    }
}
