package com.aidevcompanion.app.domain.usecase

import com.aidevcompanion.app.domain.model.ChatResult
import com.aidevcompanion.app.domain.repository.ChatRepository
import kotlinx.coroutines.flow.Flow
import javax.inject.Inject

/**
 * Use case for sending a message to the chat API.
 * Encapsulates the logic for interacting with the [ChatRepository].
 */
class SendMessageUseCase @Inject constructor(
    private val repository: ChatRepository
) {
    operator fun invoke(
        conversationId: String?,
        message: String?,
        sourceCode: String?
    ): Flow<Result<ChatResult>> {
        return repository.sendMessage(conversationId, message, sourceCode)
    }
}
