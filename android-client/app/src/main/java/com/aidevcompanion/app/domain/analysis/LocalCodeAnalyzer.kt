package com.aidevcompanion.app.domain.analysis

import javax.inject.Inject

/**
 * A pragmatic, lightweight local analyzer that performs deterministic checks
 * on code before it leaves the device.
 * 
 * Philosophy:
 * - Don't use an LLM for what a Regex can do in 1ms.
 * - Catch security risks (API keys) locally to prevent data leaks.
 * - Provide instant feedback for offline-capable tasks.
 */
open class LocalCodeAnalyzer @Inject constructor() {

    data class AnalysisResult(
        val hasCriticalIssues: Boolean,
        val issues: List<String>,
        val suggestions: List<String>
    )

    open fun analyze(code: String?): AnalysisResult {
        if (code.isNullOrBlank()) {
            return AnalysisResult(false, emptyList(), emptyList())
        }

        val issues = mutableListOf<String>()
        val suggestions = mutableListOf<String>()
        var hasCritical = false

        // 1. Security: Check for Hardcoded Secrets
        if (containsSecrets(code)) {
            issues.add("CRITICAL: Potential API Key or Secret detected in code.")
            suggestions.add("Remove hardcoded secrets before sending to AI.")
            hasCritical = true
        }

        // 2. Kotlin Specific Checks
        if (isKotlinFile(code)) {
            // Check for 'var' usage where 'val' might suffice (heuristic)
            val varCount = code.lines().count { it.trim().startsWith("var ") }
            if (varCount > 5) {
                suggestions.add("Found $varCount mutable variables ('var'). Consider using 'val' for immutability where possible.")
            }

            // Check for 'println' debugging
            if (code.contains("println(")) {
                suggestions.add("Found 'println' statements. Consider using Android 'Log.d' or Timber for production logging.")
            }
            
            // Check for GlobalScope usage (Anti-pattern)
            if (code.contains("GlobalScope")) {
                issues.add("WARNING: Usage of 'GlobalScope' detected. This can lead to memory leaks.")
                suggestions.add("Use 'viewModelScope' or 'lifecycleScope' instead.")
            }
        }

        // 3. XML / Manifest Checks
        if (isXmlFile(code)) {
            if (code.contains("android:name=\"android.permission.INTERNET\"") && !code.contains("uses-permission")) {
                 // Just a heuristic check for permission structure
            }
            
            if (code.contains("android:debuggable=\"true\"")) {
                 issues.add("SECURITY: 'android:debuggable=\"true\"' detected. Ensure this is disabled for release builds.")
            }
        }

        // 4. Pragmatism: Check for TODOs
        val todoCount = code.lines().count { it.contains("TODO", ignoreCase = true) || it.contains("FIXME", ignoreCase = true) }
        if (todoCount > 0) {
            suggestions.add("Found $todoCount TODO/FIXME items. Consider addressing these first.")
        }

        // 5. Efficiency: Check for Large Files
        if (code.length > 10_000) {
            issues.add("File is very large (${code.length} chars). Analysis may be slow.")
            suggestions.add("Consider sending only the relevant function or class.")
        }

        return AnalysisResult(hasCritical, issues, suggestions)
    }

    private fun containsSecrets(code: String): Boolean {
        val patterns = listOf(
            "AKIA[0-9A-Z]{16}".toRegex(), // AWS Access Key
            "AIza[0-9A-Za-z-_]{35}".toRegex(), // Google API Key
            "sk_live_[0-9a-zA-Z]{24}".toRegex(), // Stripe/Generic
            "ghp_[0-9a-zA-Z]{36}".toRegex() // GitHub Personal Access Token
        )
        return patterns.any { it.containsMatchIn(code) }
    }
    
    private fun isKotlinFile(code: String): Boolean {
        return code.contains("package ") || code.contains("val ") || code.contains("fun ")
    }
    
    private fun isXmlFile(code: String): Boolean {
        return code.trim().startsWith("<") || code.contains("xmlns:android")
    }

    /**
     * Attempts to extract source code from a natural language message.
     * Supports Markdown code blocks and heuristic detection.
     */
    open fun extractCode(message: String?): String? {
        if (message.isNullOrBlank()) return null

        // 1. Extract from Markdown code blocks (```code```)
        val codeBlockRegex = "```(?:kotlin|java|xml)?\\s*([\\s\\S]*?)```".toRegex()
        val match = codeBlockRegex.find(message)
        if (match != null) {
            return match.groupValues[1].trim()
        }

        // 2. Heuristic: If the message itself looks like code (and isn't just a sentence)
        if (isKotlinFile(message) || isXmlFile(message)) {
            // Ensure it's not just a short sentence containing a keyword
            if (message.length > 20 && (message.contains("{") || message.contains("</"))) {
                return message.trim()
            }
        }

        return null
    }
}
