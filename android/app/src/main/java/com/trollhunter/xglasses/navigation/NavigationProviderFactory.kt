package com.trollhunter.xglasses.navigation

import com.trollhunter.xglasses.BuildConfig

object NavigationProviderFactory {
    fun createOrNull(): NavigationProvider? {
        val geocoder = BuildConfig.XG_GEOCODER_BASE_URL.trim()
        val router = BuildConfig.XG_ROUTER_BASE_URL.trim()
        if (geocoder.isEmpty() || router.isEmpty()) return null
        return runCatching {
            OpenNavigationProvider(NavigationProviderConfig(geocoder, router))
        }.getOrNull()
    }

    fun isConfigured(): Boolean = createOrNull() != null
}
