package com.aidevcompanion.app.domain.model

data class ChatMessage(
    val id: String = java.util.UUID.randomUUID().toString(),
    val content: String,
    val isUser: Boolean,
    val isCode: Boolean = false,
    val issues: List<IssueDomain>? = null,
    val suggestedActions: List<String>? = null
)

data class IssueDomain(
    val type: String,
    val description: String,
    val suggestion: String
)

data class ChatResult(
    val conversationId: String,
    val message: ChatMessage
)
