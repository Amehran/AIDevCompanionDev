package com.aidevcompanion.app.domain.repository

import com.aidevcompanion.app.domain.model.ChatResult
import kotlinx.coroutines.flow.Flow

interface ChatRepository {
    suspend fun checkHealth(): Boolean
    fun sendMessage(
        conversationId: String?,
        message: String?,
        sourceCode: String?
    ): Flow<Result<ChatResult>>
}
