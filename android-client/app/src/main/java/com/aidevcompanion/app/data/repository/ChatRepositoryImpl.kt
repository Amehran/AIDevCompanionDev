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
                // Parse error response for better user feedback
                val errorMessage = when (response.code()) {
                    400 -> {
                        val errorBody = response.errorBody()?.string()
                        if (errorBody?.contains("source_code") == true) {
                            "Please start a new conversation by sending code in Code Mode (▶️)"
                        } else {
                            "Bad request: ${response.message()}"
                        }
                    }
                    422 -> "Invalid input. Please check your message and try again."
                    500 -> "Server error. Please try again later."
                    else -> "Error: ${response.code()} ${response.message()}"
                }
                emit(Result.failure(Exception(errorMessage)))
            }
        } catch (e: Exception) {
            emit(Result.failure(e))
        }
    }
}
