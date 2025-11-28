package com.aidevcompanion.app.data.repository

import app.cash.turbine.test
import com.aidevcompanion.app.data.model.ChatRequest
import com.aidevcompanion.app.data.model.ChatResponse
import com.aidevcompanion.app.data.model.HealthResponse
import com.aidevcompanion.app.data.remote.ApiService
import io.mockk.coEvery
import io.mockk.mockk
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
    private lateinit var repository: ChatRepositoryImpl

    @Before
    fun setUp() {
        repository = ChatRepositoryImpl(apiService)
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
        val flow = repository.sendMessage("123", "Hello", null)

        // Then
        flow.test {
            val result = awaitItem()
            assertTrue(result.isSuccess)
            assertEquals("123", result.getOrNull()?.conversationId)
            awaitComplete()
        }
    }

    @Test
    fun `sendMessage emits failure with correct message for 400 error with source_code`() = runTest {
        // Given
        val errorBody = "{\"detail\": \"Missing source_code\"}".toResponseBody("application/json".toMediaTypeOrNull())
        coEvery { apiService.chat(any()) } returns Response.error(400, errorBody)

        // When
        val flow = repository.sendMessage("123", "Hello", null)

        // Then
        flow.test {
            val result = awaitItem()
            assertTrue(result.isFailure)
            val exception = result.exceptionOrNull()
            assertTrue(exception?.message?.contains("Please start a new conversation") == true)
            awaitComplete()
        }
    }

    @Test
    fun `sendMessage emits failure with correct message for 422 error`() = runTest {
        // Given
        val errorBody = "{}".toResponseBody("application/json".toMediaTypeOrNull())
        coEvery { apiService.chat(any()) } returns Response.error(422, errorBody)

        // When
        val flow = repository.sendMessage("123", "Hello", null)

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
        val flow = repository.sendMessage("123", "Hello", null)

        // Then
        flow.test {
            val result = awaitItem()
            assertTrue(result.isFailure)
            assertEquals("Network error", result.exceptionOrNull()?.message)
            awaitComplete()
        }
    }
}
