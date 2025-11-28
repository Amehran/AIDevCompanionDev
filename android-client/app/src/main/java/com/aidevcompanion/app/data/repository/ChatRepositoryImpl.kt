package com.aidevcompanion.app.data.repository

import com.aidevcompanion.app.data.mapper.toDomain
import com.aidevcompanion.app.data.model.ChatRequest
import com.aidevcompanion.app.data.remote.ApiService
import com.aidevcompanion.app.domain.model.ChatResult
import com.aidevcompanion.app.domain.repository.ChatRepository
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.flow
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class ChatRepositoryImpl @Inject constructor(
    private val apiService: ApiService
) : ChatRepository {

    override suspend fun checkHealth(): Boolean {
        return try {
            val response = apiService.checkHealth()
            response.isSuccessful && response.body()?.status == "healthy"
        } catch (e: Exception) {
            false
        }
    }

    override fun sendMessage(
        conversationId: String?,
        message: String?,
        sourceCode: String?
    ): Flow<Result<ChatResult>> = flow {
        try {
            val request = ChatRequest(
                conversation_id = conversationId,
                message = message,
                source_code = sourceCode
            )
            val response = apiService.chat(request)
            if (response.isSuccessful && response.body() != null) {
                emit(Result.success(response.body()!!.toDomain()))
            } else {
                emit(Result.failure(Exception("Error: ${response.code()} ${response.message()}")))
            }
        } catch (e: Exception) {
            emit(Result.failure(e))
        }
    }
}
