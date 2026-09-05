package com.trollhunter.xglasses.navigation

import android.content.Context
import com.amap.api.maps.MapsInitializer
import com.amap.api.services.core.ServiceSettings

object AmapPrivacyConsent {
    private const val PREFERENCES = "xg_map_privacy"
    private const val ACCEPTED = "amap_accepted"

    fun isAccepted(context: Context): Boolean =
        context.getSharedPreferences(PREFERENCES, Context.MODE_PRIVATE).getBoolean(ACCEPTED, false)

    fun applyStoredConsent(context: Context): Boolean {
        if (!isAccepted(context)) return false
        notifySdk(context, true)
        return true
    }

    fun accept(context: Context) {
        notifySdk(context, true)
        context.getSharedPreferences(PREFERENCES, Context.MODE_PRIVATE)
            .edit()
            .putBoolean(ACCEPTED, true)
            .apply()
    }

    fun decline(context: Context) {
        notifySdk(context, false)
        context.getSharedPreferences(PREFERENCES, Context.MODE_PRIVATE)
            .edit()
            .putBoolean(ACCEPTED, false)
            .apply()
    }

    private fun notifySdk(context: Context, accepted: Boolean) {
        MapsInitializer.updatePrivacyShow(context, true, true)
        MapsInitializer.updatePrivacyAgree(context, accepted)
        ServiceSettings.updatePrivacyShow(context, true, true)
        ServiceSettings.updatePrivacyAgree(context, accepted)
    }
}
