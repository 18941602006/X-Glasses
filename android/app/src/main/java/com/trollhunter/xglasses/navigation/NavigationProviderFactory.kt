package com.trollhunter.xglasses.navigation

import com.trollhunter.xglasses.BuildConfig

object NavigationProviderFactory {
    fun createOpenOrNull(): NavigationProvider? {
        val geocoder = BuildConfig.XG_GEOCODER_BASE_URL.trim()
        val router = BuildConfig.XG_ROUTER_BASE_URL.trim()
        if (geocoder.isEmpty() || router.isEmpty()) return null
        return runCatching {
            OpenNavigationProvider(NavigationProviderConfig(geocoder, router))
        }.getOrNull()
    }

    fun createAmap(context: android.content.Context): NavigationProvider? =
        if (isAmapConfigured()) AmapNavigationProvider(context.applicationContext) else null

    fun isAmapConfigured(): Boolean = BuildConfig.XG_AMAP_CONFIGURED

    fun isConfigured(): Boolean = isAmapConfigured() || createOpenOrNull() != null
}
