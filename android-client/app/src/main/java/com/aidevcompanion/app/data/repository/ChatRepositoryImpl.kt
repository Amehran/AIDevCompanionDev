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

/**
 * Implementation of [ChatRepository] that handles data operations for chat features.
 * Uses [ApiService] for remote data fetching and handles error parsing.
 */
@Singleton
class ChatRepositoryImpl @Inject constructor(
    private val apiService: ApiService,
    private val localAnalyzer: com.aidevcompanion.app.domain.analysis.LocalCodeAnalyzer
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
            // 1. Hybrid AI: Run Local Analysis First
            // This is "Pragmatic Architecture" - we save cloud costs and latency
            // by catching obvious issues or security risks locally.
            val analysis = localAnalyzer.analyze(sourceCode)
            
            if (analysis.hasCriticalIssues) {
                // Block the request to protect the user (e.g. leaking secrets)
                val errorMsg = analysis.issues.joinToString("\n")
                emit(Result.failure(Exception(errorMsg)))
                return@flow
            }

            val request = ChatRequest(
                conversationId = conversationId,
                message = message,
                sourceCode = sourceCode
            )
            val response = apiService.chat(request)
            if (response.isSuccessful && response.body() != null) {
                emit(Result.success(response.body()!!.toDomain()))
            } else {
                val errorMessage = parseErrorResponse(response)
                emit(Result.failure(Exception(errorMessage)))
            }
        } catch (e: Exception) {
            emit(Result.failure(e))
        }
    }

    /**
     * Parses the error response from the API to provide user-friendly error messages.
     * Handles specific error codes like 400 (Bad Request) and 422 (Unprocessable Entity).
     */
    private fun parseErrorResponse(response: retrofit2.Response<*>): String {
        return when (response.code()) {
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
    }
}
