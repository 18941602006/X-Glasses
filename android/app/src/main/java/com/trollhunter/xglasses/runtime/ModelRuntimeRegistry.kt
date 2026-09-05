package com.trollhunter.xglasses.runtime

import com.trollhunter.xglasses.domain.RuntimeState
import com.trollhunter.xglasses.domain.TaskKind
import com.trollhunter.xglasses.navigation.NavigationProviderFactory

/** No model is silently downloaded, substituted, or sent to a cloud provider. */
class ModelRuntimeRegistry {
    fun inspect(): Map<TaskKind, RuntimeState> =
        TaskKind.entries.associateWith { task ->
            if (task == TaskKind.NAVIGATION && NavigationProviderFactory.isConfigured()) {
                RuntimeState.AVAILABLE
            } else {
                RuntimeState.NOT_INSTALLED
            }
        }
}
