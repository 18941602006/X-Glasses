package com.trollhunter.xglasses.navigation

import java.io.ByteArrayOutputStream
import java.net.HttpURLConnection
import java.net.URI
import java.net.URLEncoder
import java.nio.charset.StandardCharsets
import org.json.JSONObject

data class NavigationProviderConfig(
    val geocoderBaseUrl: String,
    val routerBaseUrl: String,
) {
    init {
        validateBaseUrl(geocoderBaseUrl)
        validateBaseUrl(routerBaseUrl)
    }

    private fun validateBaseUrl(value: String) {
        val uri = URI(value)
        require(uri.scheme == "https" && uri.host != null && uri.userInfo == null) { "HTTPS provider required" }
        require(uri.query == null && uri.fragment == null) { "provider base URL cannot contain query or fragment" }
    }
}

interface NavigationProvider {
    val providerId: String
    val displayName: String
    fun normalizeLocation(point: GeoPoint): GeoPoint = point
    fun search(query: String, near: GeoPoint?): List<PlaceCandidate>
    fun walkingRoute(origin: GeoPoint, destination: PlaceCandidate): WalkingRoute
}

/** Photon-compatible search plus Valhalla-compatible pedestrian routing. No public URL is hard-coded. */
class OpenNavigationProvider(private val config: NavigationProviderConfig) : NavigationProvider {
    override val providerId = "photon-valhalla"
    override val displayName = "开放地图测试服务"

    override fun search(query: String, near: GeoPoint?): List<PlaceCandidate> {
        require(query == query.trim() && query.length in 2..120) { "invalid destination query" }
        val parameters = buildList {
            add("q=${encode(query)}")
            add("limit=5")
            if (near != null) {
                add("lat=${near.latitude}")
                add("lon=${near.longitude}")
            }
        }.joinToString("&")
        val root = JSONObject(get("${config.geocoderBaseUrl.trimEnd('/')}/api?$parameters"))
        val features = root.getJSONArray("features")
        return buildList {
            for (index in 0 until minOf(features.length(), 5)) {
                val feature = features.getJSONObject(index)
                val coordinates = feature.getJSONObject("geometry").getJSONArray("coordinates")
                val properties = feature.getJSONObject("properties")
                val label = listOf("name", "street", "city", "state", "country")
                    .mapNotNull { key -> properties.optString(key).takeIf { it.isNotBlank() } }
                    .distinct()
                    .joinToString("，")
                    .take(240)
                if (label.isNotBlank()) {
                    add(
                        PlaceCandidate(
                            id = "photon-${properties.optString("osm_type")}-${properties.optLong("osm_id", index.toLong())}",
                            label = label,
                            point = GeoPoint(coordinates.getDouble(1), coordinates.getDouble(0)),
                        ),
                    )
                }
            }
        }
    }

    override fun walkingRoute(origin: GeoPoint, destination: PlaceCandidate): WalkingRoute {
        val request = JSONObject()
            .put(
                "locations",
                org.json.JSONArray()
                    .put(JSONObject().put("lat", origin.latitude).put("lon", origin.longitude))
                    .put(JSONObject().put("lat", destination.point.latitude).put("lon", destination.point.longitude)),
            )
            .put("costing", "pedestrian")
            .put("directions_options", JSONObject().put("units", "kilometers").put("language", "zh-CN"))
        val root = JSONObject(post("${config.routerBaseUrl.trimEnd('/')}/route", request.toString()))
        val trip = root.getJSONObject("trip")
        require(trip.optInt("status", -1) == 0) { "route provider reported failure" }
        val legs = trip.getJSONArray("legs")
        require(legs.length() > 0) { "route has no legs" }
        val leg = legs.getJSONObject(0)
        val shapeText = leg.getString("shape")
        val geometry = decodePolyline6(shapeText)
        val maneuvers = leg.getJSONArray("maneuvers")
        val steps = buildList {
            for (index in 0 until maneuvers.length()) {
                val item = maneuvers.getJSONObject(index)
                require(item.optString("travel_mode") == "pedestrian") { "non-pedestrian route rejected" }
                val shapeIndex = item.optInt("end_shape_index", geometry.lastIndex).coerceIn(0, geometry.lastIndex)
                val spokenInstruction = item.optString("verbal_pre_transition_instruction")
                    .takeIf { it.isNotBlank() }
                    ?: item.optString("instruction", "继续沿步行路线前进")
                add(
                    RouteStep(
                        instruction = spokenInstruction.take(300),
                        maneuver = maneuver(item.optInt("type", -1)),
                        target = geometry[shapeIndex],
                        distanceM = (item.optDouble("length", 0.0) * 1000.0).toInt().coerceIn(0, 100_000),
                    ),
                )
            }
        }
        val total = (trip.getJSONObject("summary").getDouble("length") * 1000.0).toInt().coerceAtLeast(1)
        return WalkingRoute(
            id = "valhalla-${shapeText.hashCode().toUInt().toString(16)}",
            providerId = providerId,
            destination = destination,
            steps = steps,
            geometry = geometry,
            totalDistanceM = total,
        )
    }

    private fun get(url: String): String = request(url, "GET", null)

    private fun post(url: String, body: String): String = request(url, "POST", body)

    private fun request(url: String, method: String, body: String?): String {
        val connection = URI(url).toURL().openConnection() as HttpURLConnection
        connection.connectTimeout = 5_000
        connection.readTimeout = 8_000
        connection.instanceFollowRedirects = false
        connection.requestMethod = method
        connection.setRequestProperty("Accept", "application/json")
        connection.setRequestProperty("User-Agent", "X-Glasses/0.1")
        if (body != null) {
            connection.doOutput = true
            connection.setRequestProperty("Content-Type", "application/json; charset=utf-8")
            val bytes = body.toByteArray(StandardCharsets.UTF_8)
            require(bytes.size <= 16_384) { "request too large" }
            connection.outputStream.use { it.write(bytes) }
        }
        try {
            require(connection.responseCode in 200..299) { "provider HTTP ${connection.responseCode}" }
            return connection.inputStream.use { input ->
                val output = ByteArrayOutputStream()
                val buffer = ByteArray(8192)
                while (true) {
                    val read = input.read(buffer)
                    if (read < 0) break
                    require(output.size() + read <= 1_048_576) { "provider response too large" }
                    output.write(buffer, 0, read)
                }
                output.toString(StandardCharsets.UTF_8.name())
            }
        } finally {
            connection.disconnect()
        }
    }

    private fun encode(value: String): String = URLEncoder.encode(value, StandardCharsets.UTF_8.name())

    private fun maneuver(type: Int): Maneuver = when (type) {
        4, 5, 6 -> Maneuver.ARRIVE
        2, 9, 10, 11, 12, 18, 20, 23 -> Maneuver.RIGHT
        3, 13, 14, 15, 16, 19, 21, 24 -> Maneuver.LEFT
        in 0..38 -> Maneuver.STRAIGHT
        else -> Maneuver.UNKNOWN
    }
}

internal fun decodePolyline6(value: String): List<GeoPoint> {
    val points = mutableListOf<GeoPoint>()
    var index = 0
    var latitude = 0
    var longitude = 0
    fun nextDelta(): Int {
        var result = 0
        var shift = 0
        while (index < value.length) {
            val chunk = value[index++].code - 63
            require(chunk in 0..63 && shift <= 30) { "invalid route shape" }
            result = result or ((chunk and 0x1f) shl shift)
            if (chunk < 0x20) return if (result and 1 != 0) (result shr 1).inv() else result shr 1
            shift += 5
        }
        throw IllegalArgumentException("truncated route shape")
    }
    while (index < value.length) {
        latitude += nextDelta()
        longitude += nextDelta()
        points += GeoPoint(latitude / 1_000_000.0, longitude / 1_000_000.0)
        require(points.size <= 20_000) { "route shape too large" }
    }
    require(points.size >= 2) { "route shape too short" }
    return points
}
