package com.aidevcompanion.app.data.mapper

import com.aidevcompanion.app.data.model.ChatResponse
import com.aidevcompanion.app.data.model.Issue
import com.aidevcompanion.app.domain.model.ChatMessage
import com.aidevcompanion.app.domain.model.ChatResult
import com.aidevcompanion.app.domain.model.IssueDomain

fun ChatResponse.toDomain(): ChatResult {
    return ChatResult(
        conversationId = this.conversation_id,
        message = ChatMessage(
            content = this.summary ?: this.improved_code ?: "No response",
            isUser = false,
            isCode = this.improved_code != null,
            issues = this.issues?.map { it.toDomain() },
            suggestedActions = this.suggested_actions
        )
    )
}

fun Issue.toDomain(): IssueDomain {
    return IssueDomain(
        type = this.type,
        description = this.description,
        suggestion = this.suggestion
    )
}
