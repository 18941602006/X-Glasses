plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
    id("org.jetbrains.kotlin.plugin.compose")
}

fun String.asBuildConfigString(): String = "\"" + replace("\\", "\\\\").replace("\"", "\\\"") + "\""

val xgGeocoderBaseUrl = providers.gradleProperty("XG_GEOCODER_BASE_URL").orElse("")
val xgRouterBaseUrl = providers.gradleProperty("XG_ROUTER_BASE_URL").orElse("")
val xgAmapAndroidKey = providers.gradleProperty("AMAP_ANDROID_KEY").orElse("")

android {
    namespace = "com.trollhunter.xglasses"
    compileSdk = 35
    defaultConfig {
        applicationId = "com.trollhunter.xglasses"
        minSdk = 28
        targetSdk = 35
        versionCode = 1
        versionName = "0.1.0"
        ndk { abiFilters += listOf("arm64-v8a", "armeabi-v7a") }
        testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"
        buildConfigField("String", "XG_GEOCODER_BASE_URL", xgGeocoderBaseUrl.get().asBuildConfigString())
        buildConfigField("String", "XG_ROUTER_BASE_URL", xgRouterBaseUrl.get().asBuildConfigString())
        buildConfigField("boolean", "XG_AMAP_CONFIGURED", xgAmapAndroidKey.map { it.isNotBlank() }.get().toString())
        manifestPlaceholders["AMAP_ANDROID_KEY"] = xgAmapAndroidKey.get()
    }
    buildTypes {
        release {
            isMinifyEnabled = true
            proguardFiles(getDefaultProguardFile("proguard-android-optimize.txt"), "proguard-rules.pro")
        }
    }
    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
    kotlinOptions { jvmTarget = "17" }
    buildFeatures {
        compose = true
        buildConfig = true
    }
}

dependencies {
    implementation(platform("androidx.compose:compose-bom:2025.04.01"))
    implementation("androidx.activity:activity-compose:1.10.1")
    implementation("androidx.core:core-ktx:1.16.0")
    implementation("androidx.compose.material3:material3")
    implementation("androidx.compose.ui:ui")
    implementation("androidx.compose.ui:ui-tooling-preview")
    implementation("com.amap.api:3dmap-location-search:10.1.300_loc6.4.9_sea9.7.4")
    debugImplementation("androidx.compose.ui:ui-tooling")
    testImplementation("junit:junit:4.13.2")
    androidTestImplementation(platform("androidx.compose:compose-bom:2025.04.01"))
    androidTestImplementation("androidx.compose.ui:ui-test-junit4")
    androidTestImplementation("androidx.test.ext:junit:1.2.1")
    androidTestImplementation("androidx.test.espresso:espresso-core:3.6.1")
    debugImplementation("androidx.compose.ui:ui-test-manifest")
}
