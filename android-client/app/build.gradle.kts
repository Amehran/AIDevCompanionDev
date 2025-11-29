plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
    id("com.google.dagger.hilt.android")
    id("org.jetbrains.kotlin.kapt")
    id("jacoco")
}

android {
    namespace = "com.aidevcompanion.app"
    compileSdk = 34

    defaultConfig {
        applicationId = "com.aidevcompanion.app"
        minSdk = 26
        targetSdk = 34
        versionCode = 1
        versionName = "1.0"

        testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"
        vectorDrawables {
            useSupportLibrary = true
        }
        
        // Base URL from Lambda
        buildConfigField("String", "BASE_URL", "\"https://mscwwpv7wxm4tlstkg2qjqydxa0xldaa.lambda-url.us-east-1.on.aws/\"")
    }

    buildTypes {
        release {
            isMinifyEnabled = false
            proguardFiles(getDefaultProguardFile("proguard-android-optimize.txt"), "proguard-rules.pro")
        }
        debug {
            enableUnitTestCoverage = true
        }
    }
    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
    kotlinOptions {
        jvmTarget = "17"
    }
    buildFeatures {
        compose = true
        buildConfig = true
    }
    composeOptions {
        kotlinCompilerExtensionVersion = "1.5.4"
    }
    packaging {
        resources {
            excludes += "/META-INF/{AL2.0,LGPL2.1}"
        }
    }
}

kapt {
    correctErrorTypes = true
    javacOptions {
        option("-J--add-opens=jdk.compiler/com.sun.tools.javac.code=ALL-UNNAMED")
        option("-J--add-opens=jdk.compiler/com.sun.tools.javac.comp=ALL-UNNAMED")
        option("-J--add-opens=jdk.compiler/com.sun.tools.javac.file=ALL-UNNAMED")
        option("-J--add-opens=jdk.compiler/com.sun.tools.javac.main=ALL-UNNAMED")
        option("-J--add-opens=jdk.compiler/com.sun.tools.javac.model=ALL-UNNAMED")
        option("-J--add-opens=jdk.compiler/com.sun.tools.javac.parser=ALL-UNNAMED")
        option("-J--add-opens=jdk.compiler/com.sun.tools.javac.processing=ALL-UNNAMED")
        option("-J--add-opens=jdk.compiler/com.sun.tools.javac.tree=ALL-UNNAMED")
        option("-J--add-opens=jdk.compiler/com.sun.tools.javac.util=ALL-UNNAMED")
    }
}

dependencies {
    implementation("androidx.core:core-ktx:1.12.0")
    implementation("androidx.lifecycle:lifecycle-runtime-ktx:2.6.2")
    implementation("androidx.activity:activity-compose:1.8.1")
    implementation(platform("androidx.compose:compose-bom:2023.08.00"))
    implementation("androidx.compose.ui:ui")
    implementation("androidx.compose.ui:ui-graphics")
    implementation("androidx.compose.ui:ui-tooling-preview")
    implementation("androidx.compose.material3:material3")
    
    // Navigation
    implementation("androidx.navigation:navigation-compose:2.7.5")
    
    // Networking
    implementation("com.squareup.retrofit2:retrofit:2.9.0")
    implementation("com.squareup.retrofit2:converter-gson:2.9.0")
    implementation("com.squareup.okhttp3:logging-interceptor:4.11.0")
    
    // DI - Hilt
    implementation("com.google.dagger:hilt-android:2.48")
    kapt("com.google.dagger:hilt-android-compiler:2.48")
    implementation("androidx.hilt:hilt-navigation-compose:1.1.0")
    
    // Markdown
    implementation("com.github.jeziellago:compose-markdown:0.3.7")
    
    // Room Database
    implementation("androidx.room:room-runtime:2.6.1")
    implementation("androidx.room:room-ktx:2.6.1")
    kapt("androidx.room:room-compiler:2.6.1")

    // Testing
    testImplementation("junit:junit:4.13.2")
    testImplementation("io.mockk:mockk:1.13.8")
    testImplementation("app.cash.turbine:turbine:1.0.0")
    testImplementation("org.jetbrains.kotlinx:kotlinx-coroutines-test:1.7.3")
    
    androidTestImplementation("androidx.test.ext:junit:1.1.5")
    androidTestImplementation("androidx.test.espresso:espresso-core:3.5.1")
    androidTestImplementation(platform("androidx.compose:compose-bom:2023.08.00"))
    androidTestImplementation("androidx.compose.ui:ui-test-junit4")
    debugImplementation("androidx.compose.ui:ui-tooling")
    debugImplementation("androidx.compose.ui:ui-test-manifest")
}

tasks.register<JacocoReport>("jacocoTestReport") {
    dependsOn("testDebugUnitTest")
    reports {
        xml.required.set(true)
        html.required.set(true)
    }
    
    val debugTree = fileTree("${layout.buildDirectory.get()}/tmp/kotlin-classes/debug") {
        exclude(
            "**/R.class",
            "**/R$*.class",
            "**/BuildConfig.*",
            "**/Manifest*.*",
            "**/*Test*.*",
            "android/**/*.*",
            "**/di/*",
            "**/*MapperImpl*",
            "**/*Hilt*",
            "**/hilt_aggregated_deps/**"
        )
    }
    val mainSrc = "${project.projectDir}/src/main/java"
    sourceDirectories.setFrom(files(mainSrc))
    classDirectories.setFrom(files(debugTree))
    executionData.setFrom(files("${layout.buildDirectory.get()}/outputs/unit_test_code_coverage/debugUnitTest/testDebugUnitTest.exec"))
}

java {
    toolchain {
        languageVersion.set(JavaLanguageVersion.of(17))
    }
}
