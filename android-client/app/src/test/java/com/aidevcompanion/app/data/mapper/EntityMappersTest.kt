package com.aidevcompanion.app.data.mapper

import com.aidevcompanion.app.data.local.ConversationEntity
import com.aidevcompanion.app.data.local.IssueEntity
import com.aidevcompanion.app.data.local.MessageEntity
import com.aidevcompanion.app.domain.model.ChatMessage
import com.aidevcompanion.app.domain.model.IssueDomain
import com.aidevcompanion.app.ui.viewmodel.ChatUiState
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertNull
import org.junit.Test

class EntityMappersTest {

    @Test
    fun `toEntity maps IssueDomain to IssueEntity correctly`() {
        // Given
        val issueDomain = IssueDomain(
            type = "bug",
            description = "NPE",
            suggestion = "Check for null"
        )

        // When
        val entity = issueDomain.toEntity()

        // Then
        assertEquals("bug", entity.type)
        assertEquals("NPE", entity.description)
        assertEquals("Check for null", entity.suggestion)
    }

    @Test
    fun `toEntity maps ChatMessage to MessageEntity correctly`() {
        // Given
        val chatMessage = ChatMessage(
            content = "Hello",
            isUser = true,
            isCode = false
        )

        // When
        val entity = chatMessage.toEntity()

        // Then
        assertEquals("user", entity.role)
        assertEquals("Hello", entity.content)
        assertEquals(false, entity.isCode)
    }

    @Test
    fun `toConversationEntity returns null when conversationId is null`() {
        // Given
        val uiState = ChatUiState(conversationId = null)

        // When
        val entity = uiState.toConversationEntity()

        // Then
        assertNull(entity)
    }

    @Test
    fun `toConversationEntity maps ChatUiState to ConversationEntity correctly`() {
        // Given
        val message = ChatMessage(content = "Hi", isUser = true)
        val uiState = ChatUiState(
            conversationId = "123",
            messages = listOf(message)
        )

        // When
        val entity = uiState.toConversationEntity()

        // Then
        assertNotNull(entity)
        assertEquals("123", entity?.id)
        assertEquals(1, entity?.messages?.size)
        assertEquals("user", entity?.messages?.first()?.role)
    }
}
