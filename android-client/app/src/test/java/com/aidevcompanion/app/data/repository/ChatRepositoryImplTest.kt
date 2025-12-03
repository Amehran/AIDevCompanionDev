package com.aidevcompanion.app.data.repository

import app.cash.turbine.test
import com.aidevcompanion.app.data.model.ChatRequest
import com.aidevcompanion.app.data.model.ChatResponse
import com.aidevcompanion.app.data.model.HealthResponse
import com.aidevcompanion.app.data.remote.ApiService
import com.aidevcompanion.app.domain.analysis.LocalCodeAnalyzer
import com.aidevcompanion.app.domain.model.ChatMessage
import io.mockk.coEvery
import io.mockk.every
import io.mockk.mockk
import io.mockk.coVerify
import io.mockk.slot
import kotlinx.coroutines.test.runTest
import okhttp3.MediaType.Companion.toMediaTypeOrNull
import okhttp3.ResponseBody.Companion.toResponseBody
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Test
import retrofit2.Response

class ChatRepositoryImplTest {

    private val apiService: ApiService = mockk()
    private val localAnalyzer: LocalCodeAnalyzer = mockk()
    private lateinit var repository: ChatRepositoryImpl

    @Before
    fun setUp() {
        // Default behavior: No issues found locally, no code extracted
        every { localAnalyzer.analyze(any()) } returns LocalCodeAnalyzer.AnalysisResult(false, emptyList(), emptyList())
        every { localAnalyzer.extractCode(any()) } returns null
        repository = ChatRepositoryImpl(apiService, localAnalyzer)
    }

    @Test
    fun `checkHealth returns true when API is healthy`() = runTest {
        // Given
        val response = Response.success(HealthResponse(status = "healthy", service = "ai-dev-companion"))
        coEvery { apiService.checkHealth() } returns response

        // When
        val result = repository.checkHealth()

        // Then
        assertTrue(result)
    }

    @Test
    fun `checkHealth returns false when API is unhealthy`() = runTest {
        // Given
        val response = Response.success(HealthResponse(status = "unhealthy", service = "ai-dev-companion"))
        coEvery { apiService.checkHealth() } returns response

        // When
        val result = repository.checkHealth()

        // Then
        assertFalse(result)
    }

    @Test
    fun `checkHealth returns false when API call fails`() = runTest {
        // Given
        coEvery { apiService.checkHealth() } throws Exception("Network error")

        // When
        val result = repository.checkHealth()

        // Then
        assertFalse(result)
    }

    @Test
    fun `sendMessage blocks request when local analyzer finds critical issues`() = runTest {
        // Given
        val criticalIssue = "CRITICAL: Secret detected"
        every { localAnalyzer.analyze(any()) } returns LocalCodeAnalyzer.AnalysisResult(
            hasCriticalIssues = true,
            issues = listOf(criticalIssue),
            suggestions = emptyList()
        )

        // When
        val flow = repository.sendMessage("123", "Hello", "val key = \"AKIA...\"")

        // Then
        flow.test {
            val result = awaitItem()
            assertTrue(result.isFailure)
            assertEquals(criticalIssue, result.exceptionOrNull()?.message)
            awaitComplete()
        }
        
        // Verify API was NOT called (Efficiency/Security check)
        coVerify(exactly = 0) { apiService.chat(any()) }
    }

    @Test
    fun `sendMessage responds locally when no code is present`() = runTest {
        // Given
        val message = "Hi there"
        every { localAnalyzer.extractCode(message) } returns null

        // When
        val flow = repository.sendMessage("123", message, null)

        // Then
        flow.test {
            val result = awaitItem()
            assertTrue(result.isSuccess)
            val chatResult = result.getOrNull()
            assertFalse(chatResult?.message?.isUser ?: true)
            assertTrue(chatResult?.message?.content?.contains("Hello! I'm your AI Code Companion") == true)
            awaitComplete()
        }
        
        // Verify API was NOT called
        coVerify(exactly = 0) { apiService.chat(any()) }
    }

    @Test
    fun `sendMessage responds locally to thanks`() = runTest {
        // Given
        val message = "Thanks for the help"
        every { localAnalyzer.extractCode(message) } returns null

        // When
        val flow = repository.sendMessage("123", message, null)

        // Then
        flow.test {
            val result = awaitItem()
            assertTrue(result.isSuccess)
            val chatResult = result.getOrNull()
            assertFalse(chatResult?.message?.isUser ?: true)
            assertTrue(chatResult?.message?.content?.contains("You're welcome") == true)
            awaitComplete()
        }
        
        // Verify API was NOT called
        coVerify(exactly = 0) { apiService.chat(any()) }
    }

    @Test
    fun `sendMessage extracts code and sends to API`() = runTest {
        // Given
        val message = "Check this: ```fun test() {}```"
        val extractedCode = "fun test() {}"
        every { localAnalyzer.extractCode(message) } returns extractedCode
        
        val chatResponse = ChatResponse(
            conversationId = "123",
            summary = "Summary",
            issues = emptyList(),
            improvedCode = null,
            awaitingUserInput = false,
            suggestedActions = null
        )
        coEvery { apiService.chat(any()) } returns Response.success(chatResponse)

        // When
        val flow = repository.sendMessage("123", message, null)

        // Then
        flow.test {
            val result = awaitItem()
            assertTrue(result.isSuccess)
            awaitComplete()
        }
        
        // Verify API WAS called with extracted code
        val slot = slot<ChatRequest>()
        coVerify(exactly = 1) { apiService.chat(capture(slot)) }
        assertEquals(extractedCode, slot.captured.sourceCode)
    }

    @Test
    fun `sendMessage emits success when API call is successful`() = runTest {
        // Given
        val chatResponse = ChatResponse(
            conversationId = "123",
            summary = "Summary",
            issues = emptyList(),
            improvedCode = null,
            awaitingUserInput = false,
            suggestedActions = null
        )
        coEvery { apiService.chat(any()) } returns Response.success(chatResponse)

        // When
        val flow = repository.sendMessage("123", "Hello", "fun test(){}")

        // Then
        flow.test {
            val result = awaitItem()
            assertTrue(result.isSuccess)
            assertEquals("123", result.getOrNull()?.conversationId)
            awaitComplete()
        }
    }

    @Test
    fun `sendMessage emits failure with correct message for 422 error`() = runTest {
        // Given
        val errorBody = "{}".toResponseBody("application/json".toMediaTypeOrNull())
        coEvery { apiService.chat(any()) } returns Response.error(422, errorBody)

        // When
        // Must provide sourceCode to bypass local check
        val flow = repository.sendMessage("123", "Hello", "fun test(){}")

        // Then
        flow.test {
            val result = awaitItem()
            assertTrue(result.isFailure)
            assertEquals("Invalid input. Please check your message and try again.", result.exceptionOrNull()?.message)
            awaitComplete()
        }
    }

    @Test
    fun `sendMessage emits failure when API call throws exception`() = runTest {
        // Given
        coEvery { apiService.chat(any()) } throws Exception("Network error")

        // When
        // Must provide sourceCode to bypass local check
        val flow = repository.sendMessage("123", "Hello", "fun test(){}")

        // Then
        flow.test {
            val result = awaitItem()
            assertTrue(result.isFailure)
            assertEquals("Network error", result.exceptionOrNull()?.message)
            awaitComplete()
        }
    }
}
