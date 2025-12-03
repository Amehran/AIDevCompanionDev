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
            // 1. Hybrid AI: Code Extraction
            // If the user didn't explicitly use "Code Mode" but pasted code in the message, extract it.
            var finalSourceCode = sourceCode
            if (finalSourceCode.isNullOrBlank()) {
                finalSourceCode = localAnalyzer.extractCode(message)
            }

            // 2. Hybrid AI: Local vs Cloud Routing
            // If we still have no code, this is a "Normal Conversation".
            // As per architecture, handle this LOCALLY to save cost/latency.
            if (finalSourceCode.isNullOrBlank()) {
                // Simulate local AI response (Pragmatic approach: Rule-based for now)
                val localResponse = when {
                    message?.contains("hi", ignoreCase = true) == true -> "Hello! I'm your AI Code Companion. Share some Kotlin code, and I'll analyze it for you."
                    message?.contains("help", ignoreCase = true) == true -> "I can help you optimize Kotlin code, find bugs, and check for security issues. Just paste your code!"
                    else -> "I'm tuned to analyze code. Please paste a snippet or use Code Mode (▶️)."
                }
                
                emit(Result.success(ChatResult(
                    conversationId = conversationId ?: java.util.UUID.randomUUID().toString(),
                    message = com.aidevcompanion.app.domain.model.ChatMessage(
                        content = localResponse,
                        isUser = false
                    )
                )))
                return@flow
            }

            // 3. Hybrid AI: Run Local Analysis First (on the code we found)
            val analysis = localAnalyzer.analyze(finalSourceCode)
            
            if (analysis.hasCriticalIssues) {
                // Block the request to protect the user (e.g. leaking secrets)
                val errorMsg = analysis.issues.joinToString("\n")
                emit(Result.failure(Exception(errorMsg)))
                return@flow
            }

            val request = ChatRequest(
                conversationId = conversationId,
                message = message,
                sourceCode = finalSourceCode // Use the extracted code
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
