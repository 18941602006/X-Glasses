package com.trollhunter.xglasses.runtime

import com.trollhunter.xglasses.domain.RuntimeState
import com.trollhunter.xglasses.domain.TaskKind

/** No model is silently downloaded, substituted, or sent to a cloud provider. */
class ModelRuntimeRegistry {
    fun inspect(): Map<TaskKind, RuntimeState> =
        TaskKind.entries.associateWith { RuntimeState.NOT_INSTALLED }
}
