pluginManagement {
    repositories {
        google()
        mavenCentral()
        gradlePluginPortal()
    }
    plugins {
        id("com.android.application") version "8.2.0"
        id("org.jetbrains.kotlin.android") version "1.9.20"
        id("com.google.dagger.hilt.android") version "2.48"
        id("org.jetbrains.kotlin.kapt") version "1.9.20" // <-- Add this line
    }
}
dependencyResolutionManagement {
    repositoriesMode.set(RepositoriesMode.FAIL_ON_PROJECT_REPOS)
    repositories {
        google()
        mavenCentral()
        maven { url = uri("https://jitpack.io") } // For compose-markdown
    }
}

rootProject.name = "AIDevCompanion"
include(":app")
