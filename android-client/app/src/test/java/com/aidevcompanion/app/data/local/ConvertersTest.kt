package com.aidevcompanion.app.data.local

import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Test

class ConvertersTest {

    private val converters = Converters()

    @Test
    fun `fromIssueList converts list to JSON string`() {
        val issues = listOf(
            IssueEntity("bug", "desc", "fix"),
            IssueEntity("perf", "slow", "optimize")
        )
        val json = converters.fromIssueList(issues)
        assertEquals("[{\"type\":\"bug\",\"description\":\"desc\",\"suggestion\":\"fix\"},{\"type\":\"perf\",\"description\":\"slow\",\"suggestion\":\"optimize\"}]", json)
    }

    @Test
    fun `fromIssueList returns null for null input`() {
        assertNull(converters.fromIssueList(null))
    }

    @Test
    fun `toIssueList converts JSON string to list`() {
        val json = "[{\"type\":\"bug\",\"description\":\"desc\",\"suggestion\":\"fix\"}]"
        val issues = converters.toIssueList(json)
        assertEquals(1, issues?.size)
        assertEquals("bug", issues?.get(0)?.type)
    }

    @Test
    fun `toIssueList returns null for null input`() {
        assertNull(converters.toIssueList(null))
    }

    @Test
    fun `fromMessageList converts list to JSON string`() {
        val messages = listOf(
            MessageEntity("user", "hello", false, 1000L)
        )
        val json = converters.fromMessageList(messages)
        assertEquals("[{\"role\":\"user\",\"content\":\"hello\",\"isCode\":false,\"timestamp\":1000}]", json)
    }

    @Test
    fun `toMessageList converts JSON string to list`() {
        val json = "[{\"role\":\"user\",\"content\":\"hello\",\"isCode\":false,\"timestamp\":1000}]"
        val messages = converters.toMessageList(json)
        assertEquals(1, messages.size)
        assertEquals("user", messages[0].role)
        assertEquals(1000L, messages[0].timestamp)
    }
}
