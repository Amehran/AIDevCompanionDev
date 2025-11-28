package com.aidevcompanion.app.data.model

data class ChatRequest(
    val source_code: String? = null,
    val conversation_id: String? = null,
    val message: String? = null,
    val apply_improvements: Boolean? = null
)

data class ChatResponse(
    val conversation_id: String,
    val summary: String?,
    val issues: List<Issue>?,
    val improved_code: String?,
    val awaiting_user_input: Boolean,
    val suggested_actions: List<String>?
)

data class Issue(
    val type: String,
    val description: String,
    val suggestion: String
)

data class HealthResponse(
    val status: String,
    val service: String
)
