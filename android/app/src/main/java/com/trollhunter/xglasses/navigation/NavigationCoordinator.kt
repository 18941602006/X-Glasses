package com.trollhunter.xglasses.navigation

import android.os.SystemClock
import java.io.Closeable
import java.util.concurrent.Executors
import java.util.concurrent.atomic.AtomicBoolean

class NavigationCoordinator(
    context: android.content.Context,
    initialProvider: NavigationProvider?,
    providerName: String,
    privacyConsentRequired: Boolean,
    privacyConsentGranted: Boolean,
    private val publish: (NavigationUiState) -> Unit,
    private val onTaskFailed: (String) -> Unit,
    private val onArrived: () -> Unit,
) : Closeable {
    private val engine = NavigationEngine()
    private val executor = Executors.newSingleThreadExecutor()
    private val closed = AtomicBoolean(false)
    private val locationSource = AndroidLocationSource(context, ::onFix, ::onLocationUnavailable)
    @Volatile
    private var provider: NavigationProvider? = initialProvider
    @Volatile
    private var state = NavigationUiState(
        providerConfigured = initialProvider != null,
        providerName = providerName,
        privacyConsentRequired = privacyConsentRequired,
        privacyConsentGranted = privacyConsentGranted,
    )
    private var lastRawFix: LocationFix? = null
    private var lastFix: LocationFix? = null
    private var rerouteInFlight = false
    private var arrivalReported = false

    fun state(): NavigationUiState = state

    fun configureProvider(nextProvider: NavigationProvider, privacyGranted: Boolean) {
        provider = nextProvider
        lastFix = lastRawFix?.let { it.copy(point = nextProvider.normalizeLocation(it.point)) }
        update(
            state.copy(
                providerConfigured = true,
                providerName = nextProvider.displayName,
                privacyConsentGranted = privacyGranted,
                error = null,
            ),
        )
    }

    fun rejectPrivacyConsent() {
        locationSource.stop()
        rerouteInFlight = false
        provider = null
        lastRawFix = null
        lastFix = null
        update(
            state.copy(
                providerConfigured = false,
                privacyConsentGranted = false,
                routeLoading = false,
                guidance = engine.stop(),
                error = "未同意地图服务隐私条款，导航保持关闭",
            ),
        )
    }

    fun reportError(message: String) = update(state.copy(error = message.take(120)))

    fun setPermission(granted: Boolean) {
        update(state.copy(locationPermissionGranted = granted, error = if (granted) null else "需要位置权限才能导航"))
        if (granted) locationSource.start() else locationSource.stop()
    }

    fun resumeLocation() {
        if (state.locationPermissionGranted) locationSource.start()
    }

    fun pauseLocation() = locationSource.stop()

    fun setQuery(value: String) = update(state.copy(query = value.take(120), error = null))

    fun search() {
        val activeProvider = provider ?: return update(state.copy(error = "地图服务尚未配置"))
        val query = state.query.trim()
        if (query.length < 2) return update(state.copy(error = "请输入至少两个字的目的地"))
        update(state.copy(searching = true, candidates = emptyList(), selected = null, error = null))
        executor.execute {
            runCatching { activeProvider.search(query, lastFix?.point) }
                .onSuccess { results -> update(state.copy(searching = false, candidates = results, error = if (results.isEmpty()) "没有找到目的地" else null)) }
                .onFailure { update(state.copy(searching = false, error = "目的地搜索失败：${safeReason(it)}")) }
        }
    }

    fun select(candidate: PlaceCandidate) = update(state.copy(selected = candidate, error = null))

    fun start(glassesReady: Boolean) {
        if (!glassesReady) return update(state.copy(error = "眼镜风险监测未就绪，不能开始导航"))
        if (!state.locationPermissionGranted) return update(state.copy(error = "需要位置权限才能开始导航"))
        val activeProvider = provider ?: return update(state.copy(error = "地图服务尚未配置"))
        val destination = state.selected ?: return update(state.copy(error = "请先选择目的地"))
        val origin = lastFix
        val now = SystemClock.elapsedRealtime()
        if (origin == null || !origin.isUsable(now, 10_000, 50f)) {
            return update(state.copy(error = "当前位置不可用，请到开阔处等待定位"))
        }
        engine.routing(destination, now)
        arrivalReported = false
        update(state.copy(routeLoading = true, guidance = engine.snapshot, error = null))
        requestRoute(activeProvider, origin.point, destination)
    }

    fun stop() {
        rerouteInFlight = false
        update(state.copy(routeLoading = false, guidance = engine.stop(), error = null))
    }

    private fun requestRoute(activeProvider: NavigationProvider, origin: GeoPoint, destination: PlaceCandidate) {
        executor.execute {
            runCatching { activeProvider.walkingRoute(origin, destination) }
                .onSuccess { route ->
                    rerouteInFlight = false
                    update(state.copy(routeLoading = false, guidance = engine.start(route, SystemClock.elapsedRealtime()), error = null))
                }
                .onFailure {
                    rerouteInFlight = false
                    update(state.copy(routeLoading = false, guidance = engine.fail("route_failure", SystemClock.elapsedRealtime()), error = "路线规划失败：${safeReason(it)}"))
                    onTaskFailed("route_failure")
                }
        }
    }

    private fun onFix(fix: LocationFix) {
        lastRawFix = fix
        val normalized = provider?.let { fix.copy(point = it.normalizeLocation(fix.point)) } ?: fix
        lastFix = normalized
        val now = SystemClock.elapsedRealtime()
        val guidance = engine.update(normalized, now)
        update(state.copy(guidance = guidance, error = if (guidance.status == GuidanceStatus.PAUSED) guidance.instruction else state.error))
        if (guidance.status == GuidanceStatus.REROUTE_REQUIRED && !rerouteInFlight) {
            val activeProvider = provider ?: return
            val destination = state.selected ?: return
            rerouteInFlight = true
            update(state.copy(routeLoading = true))
            requestRoute(activeProvider, normalized.point, destination)
        }
        if (guidance.status == GuidanceStatus.ARRIVED && !arrivalReported) {
            arrivalReported = true
            onArrived()
        }
    }

    private fun onLocationUnavailable(reason: String) {
        update(state.copy(error = "定位服务不可用：${reason.take(80)}"))
    }

    private fun update(next: NavigationUiState) {
        if (closed.get()) return
        state = next
        publish(next)
    }

    private fun safeReason(error: Throwable): String = error.message?.take(100) ?: error::class.java.simpleName

    override fun close() {
        if (!closed.compareAndSet(false, true)) return
        locationSource.stop()
        executor.shutdownNow()
    }
}
