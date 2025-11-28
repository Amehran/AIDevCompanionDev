package com.aidevcompanion.app.data.model

import com.google.gson.annotations.SerializedName

data class ChatRequest(
    @SerializedName("source_code") val sourceCode: String? = null,
    @SerializedName("conversation_id") val conversationId: String? = null,
    val message: String? = null,
    @SerializedName("apply_improvements") val applyImprovements: Boolean? = null
)

data class ChatResponse(
    @SerializedName("conversation_id") val conversationId: String,
    val summary: String?,
    val issues: List<Issue>?,
    @SerializedName("improved_code") val improvedCode: String?,
    @SerializedName("awaiting_user_input") val awaitingUserInput: Boolean,
    @SerializedName("suggested_actions") val suggestedActions: List<String>?
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
