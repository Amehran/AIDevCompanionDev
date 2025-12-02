package com.aidevcompanion.app.ui.viewmodel

import app.cash.turbine.test
import com.aidevcompanion.app.domain.model.ChatMessage
import com.aidevcompanion.app.domain.model.ChatResult
import com.aidevcompanion.app.domain.usecase.CheckHealthUseCase
import com.aidevcompanion.app.domain.usecase.SendMessageUseCase
import io.mockk.coEvery
import io.mockk.every
import io.mockk.mockk
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.flow.flowOf
import kotlinx.coroutines.test.StandardTestDispatcher
import kotlinx.coroutines.test.resetMain
import kotlinx.coroutines.test.runTest
import kotlinx.coroutines.test.setMain
import org.junit.After
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Test

@OptIn(ExperimentalCoroutinesApi::class)
class ChatViewModelTest {

    private val sendMessageUseCase: SendMessageUseCase = mockk()
    private val checkHealthUseCase: CheckHealthUseCase = mockk()
    private val conversationDao: com.aidevcompanion.app.data.local.ConversationDao = mockk(relaxed = true)
    private lateinit var viewModel: ChatViewModel
    private val testDispatcher = StandardTestDispatcher()

    @Before
    fun setUp() {
        Dispatchers.setMain(testDispatcher)
        io.mockk.mockkStatic(android.util.Log::class)
        every { android.util.Log.d(any(), any()) } returns 0
        every { android.util.Log.e(any(), any(), any()) } returns 0
        
        // Default behavior for init block
        coEvery { checkHealthUseCase() } returns true
        viewModel = ChatViewModel(sendMessageUseCase, checkHealthUseCase, conversationDao)
    }

    @After
    fun tearDown() {
        Dispatchers.resetMain()
    }

    @Test
    fun `init checks connection and updates state`() = runTest {
        viewModel.uiState.test {
            // Initial state from init block
            val initialState = awaitItem()
            assertFalse(initialState.isLoading)
            assertTrue(initialState.isConnected)
        }
    }

    @Test
    fun `sendMessage updates state with user message and then ai response`() = runTest {
        // Given
        val userMessage = "Hello"
        val aiResponse = "Hi there"
        val chatResult = ChatResult(
            conversationId = "new_id",
            message = ChatMessage(content = aiResponse, isUser = false)
        )
        
        every { sendMessageUseCase(any(), any(), any()) } returns flowOf(Result.success(chatResult))

        viewModel.uiState.test {
            skipItems(1) // Skip initial state

            // When
            viewModel.sendMessage(userMessage)

            // Then
            // 1. Loading state with user message
            val loadingState = awaitItem()
            assertTrue(loadingState.isLoading)
            assertEquals(1, loadingState.messages.size)
            assertEquals(userMessage, loadingState.messages.first().content)

            // 2. Success state with AI response
            val successState = awaitItem()
            assertFalse(successState.isLoading)
            assertEquals(2, successState.messages.size)
            assertEquals(aiResponse, successState.messages.last().content)
            assertEquals("new_id", successState.conversationId)
            
            // Verify DB insertion
            io.mockk.coVerify(exactly = 1) { conversationDao.insertConversation(any()) }
        }
    }

    @Test
    fun `sendMessage handles error`() = runTest {
        // Given
        val errorMessage = "Network error"
        every { sendMessageUseCase(any(), any(), any()) } returns flowOf(Result.failure(Exception(errorMessage)))

        viewModel.uiState.test {
            skipItems(1) // Skip initial state

            // When
            viewModel.sendMessage("Hello")

            // Then
            // 1. Loading state
            awaitItem()

            // 2. Error state
            val errorState = awaitItem()
            assertFalse(errorState.isLoading)
            assertEquals(errorMessage, errorState.error)
        }
    }
}
