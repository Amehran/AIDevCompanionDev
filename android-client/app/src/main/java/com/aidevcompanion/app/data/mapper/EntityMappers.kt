package com.aidevcompanion.app.data.mapper

import com.aidevcompanion.app.data.local.ConversationEntity
import com.aidevcompanion.app.data.local.IssueEntity
import com.aidevcompanion.app.data.local.MessageEntity
import com.aidevcompanion.app.domain.model.ChatMessage
import com.aidevcompanion.app.domain.model.IssueDomain
import com.aidevcompanion.app.ui.viewmodel.ChatUiState

/**
 * Converts the current UI state into a database entity for local storage.
 * Returns null if there is no active conversation ID.
 */
fun ChatUiState.toConversationEntity(): ConversationEntity? {
    if (this.conversationId == null) return null
    
    return ConversationEntity(
        id = this.conversationId,
        originalCode = this.messages.firstOrNull { it.isCode && it.isUser }?.content,
        detectedIssues = this.messages
            .firstOrNull { !it.isUser && it.issues != null }
            ?.issues
            ?.map { it.toEntity() },
        messages = this.messages.map { it.toEntity() },
        createdAt = System.currentTimeMillis(),
        updatedAt = System.currentTimeMillis()
    )
}

/**
 * Maps a domain issue to a database entity.
 */
fun IssueDomain.toEntity(): IssueEntity {
    return IssueEntity(
        type = this.type,
        description = this.description,
        suggestion = this.suggestion
    )
}

/**
 * Maps a domain chat message to a database entity.
 */
fun ChatMessage.toEntity(): MessageEntity {
    return MessageEntity(
        role = if (this.isUser) "user" else "assistant",
        content = this.content,
        isCode = this.isCode
    )
}

/**
 * Converts a stored conversation entity back into a list of UI-ready chat messages.
 * Note: Issues and suggested actions are not currently persisted in the message list itself.
 */
fun ConversationEntity.toUiMessages(): List<ChatMessage> {
    return this.messages.map { messageEntity ->
        ChatMessage(
            content = messageEntity.content,
            isUser = messageEntity.role == "user",
            isCode = messageEntity.isCode,
            issues = null, // Issues are stored separately in the entity if needed, or could be re-associated
            suggestedActions = null
        )
    }
}
