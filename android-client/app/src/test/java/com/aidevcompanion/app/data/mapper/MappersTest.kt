package com.aidevcompanion.app.data.mapper

import com.aidevcompanion.app.data.model.ChatResponse
import com.aidevcompanion.app.data.model.Issue
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class MappersTest {

    @Test
    fun `toDomain maps ChatResponse with improvedCode correctly`() {
        val response = ChatResponse(
            conversationId = "123",
            summary = "Summary",
            improvedCode = "fun main() {}",
            issues = null,
            awaitingUserInput = false,
            suggestedActions = null
        )

        val result = response.toDomain()

        assertEquals("123", result.conversationId)
        assertEquals("fun main() {}", result.message.content)
        assertTrue(result.message.isCode)
        assertFalse(result.message.isUser)
    }

    @Test
    fun `toDomain maps ChatResponse with summary only correctly`() {
        val response = ChatResponse(
            conversationId = "123",
            summary = "Summary",
            improvedCode = null,
            issues = null,
            awaitingUserInput = false,
            suggestedActions = null
        )

        val result = response.toDomain()

        assertEquals("123", result.conversationId)
        assertEquals("Summary", result.message.content)
        assertFalse(result.message.isCode)
    }

    @Test
    fun `toDomain maps ChatResponse with issues correctly`() {
        val issues = listOf(
            Issue("bug", "desc", "fix")
        )
        val response = ChatResponse(
            conversationId = "123",
            summary = "Summary",
            improvedCode = null,
            issues = issues,
            awaitingUserInput = false,
            suggestedActions = listOf("Fix it")
        )

        val result = response.toDomain()

        assertEquals(1, result.message.issues?.size)
        assertEquals("bug", result.message.issues?.get(0)?.type)
        assertEquals("Fix it", result.message.suggestedActions?.get(0))
    }

    @Test
    fun `Issue toDomain maps correctly`() {
        val issue = Issue("bug", "desc", "fix")
        val domain = issue.toDomain()

        assertEquals("bug", domain.type)
        assertEquals("desc", domain.description)
        assertEquals("fix", domain.suggestion)
    }
}
