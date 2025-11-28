package com.aidevcompanion.app.domain.usecase

import com.aidevcompanion.app.domain.model.ChatMessage
import com.aidevcompanion.app.domain.model.ChatResult
import com.aidevcompanion.app.domain.repository.ChatRepository
import io.mockk.every
import io.mockk.mockk
import io.mockk.verify
import kotlinx.coroutines.flow.flowOf
import kotlinx.coroutines.test.runTest
import org.junit.Assert.assertEquals
import org.junit.Test

class SendMessageUseCaseTest {

    private val repository: ChatRepository = mockk()
    private val sendMessageUseCase = SendMessageUseCase(repository)

    @Test
    fun `invoke calls repository with correct parameters`() = runTest {
        // Given
        val conversationId = "123"
        val message = "Hello"
        val sourceCode = null
        val expectedResult = Result.success(
            ChatResult(
                conversationId = "123",
                message = ChatMessage(content = "Hi", isUser = false)
            )
        )
        every { repository.sendMessage(conversationId, message, sourceCode) } returns flowOf(expectedResult)

        // When
        val resultFlow = sendMessageUseCase(conversationId, message, sourceCode)

        // Then
        resultFlow.collect { result ->
            assertEquals(expectedResult, result)
        }
        verify(exactly = 1) { repository.sendMessage(conversationId, message, sourceCode) }
    }
}
