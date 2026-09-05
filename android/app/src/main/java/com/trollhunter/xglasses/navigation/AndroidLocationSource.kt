package com.trollhunter.xglasses.navigation

import android.annotation.SuppressLint
import android.content.Context
import android.location.Location
import android.location.LocationListener
import android.location.LocationManager
import android.os.Bundle

class AndroidLocationSource(
    context: Context,
    private val onFix: (LocationFix) -> Unit,
    private val onUnavailable: (String) -> Unit,
) : LocationListener {
    private val manager = context.getSystemService(LocationManager::class.java)
    private var running = false

    @SuppressLint("MissingPermission")
    fun start() {
        if (running) return
        val providers = listOf(LocationManager.GPS_PROVIDER, LocationManager.NETWORK_PROVIDER)
            .filter { manager.isProviderEnabled(it) }
        if (providers.isEmpty()) {
            onUnavailable("location_provider_disabled")
            return
        }
        running = true
        providers.forEach { manager.requestLocationUpdates(it, 1_000L, 1f, this) }
    }

    fun stop() {
        if (!running) return
        manager.removeUpdates(this)
        running = false
    }

    override fun onLocationChanged(location: Location) {
        onFix(
            LocationFix(
                GeoPoint(location.latitude, location.longitude),
                location.accuracy,
                location.elapsedRealtimeNanos / 1_000_000,
            ),
        )
    }

    override fun onProviderDisabled(provider: String) = onUnavailable("provider_disabled:$provider")
    override fun onProviderEnabled(provider: String) = Unit
    @Deprecated("Deprecated in Android")
    override fun onStatusChanged(provider: String?, status: Int, extras: Bundle?) = Unit
}
