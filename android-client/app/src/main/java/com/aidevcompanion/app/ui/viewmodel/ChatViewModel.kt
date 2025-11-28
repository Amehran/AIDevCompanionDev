package com.aidevcompanion.app.ui.viewmodel

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.aidevcompanion.app.domain.model.ChatMessage
import com.aidevcompanion.app.domain.usecase.CheckHealthUseCase
import com.aidevcompanion.app.domain.usecase.SendMessageUseCase
import com.aidevcompanion.app.data.mapper.toConversationEntity
import com.aidevcompanion.app.data.mapper.toUiMessages
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.receiveAsFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import javax.inject.Inject

data class ChatUiState(
    val messages: List<ChatMessage> = emptyList(),
    val isLoading: Boolean = false,
    val error: String? = null,
    val isConnected: Boolean = false,
    val conversationId: String? = null
)

/**
 * ViewModel for the Chat screen.
 * Handles user interactions, manages chat state, and coordinates with use cases and repositories.
 */
@HiltViewModel
class ChatViewModel @Inject constructor(
    private val sendMessageUseCase: SendMessageUseCase,
    private val checkHealthUseCase: CheckHealthUseCase,
    private val conversationDao: com.aidevcompanion.app.data.local.ConversationDao
) : ViewModel() {

    private val _uiState = MutableStateFlow(ChatUiState())
    val uiState: StateFlow<ChatUiState> = _uiState.asStateFlow()

    private val _uiEvent = kotlinx.coroutines.channels.Channel<String>()
    val uiEvent = _uiEvent.receiveAsFlow()

    init {
        checkConnection()
    }

    fun checkConnection() {
        viewModelScope.launch {
            _uiState.update { it.copy(isLoading = true) }
            val isConnected = checkHealthUseCase()
            _uiState.update { it.copy(isLoading = false, isConnected = isConnected) }
        }
    }

    /**
     * Sends a message to the AI assistant.
     * Automatically detects if the message is code or text.
     * Updates the UI state with the user's message immediately, then launches a coroutine to fetch the response.
     */
    fun sendMessage(text: String) {
        android.util.Log.d("ChatViewModel", "sendMessage called with text: $text")

        // Auto-detect if this is code or a message
        val isCode = detectIfCode(text)
        android.util.Log.d("ChatViewModel", "Auto-detected isCode: $isCode")

        val userMessage = ChatMessage(content = text, isUser = true, isCode = isCode)
        _uiState.update { 
            it.copy(
                messages = it.messages + userMessage,
                isLoading = true,
                error = null
            ) 
        }
        android.util.Log.d("ChatViewModel", "UI state updated with user message. Current messages count: ${_uiState.value.messages.size}")

        viewModelScope.launch {
            android.util.Log.d("ChatViewModel", "Launching sendMessageUseCase")
            sendMessageUseCase(
                conversationId = _uiState.value.conversationId,
                message = if (!isCode) text else null,
                sourceCode = if (isCode) text else null
            ).collect { result ->
                result.onSuccess { chatResult ->
                    android.util.Log.d("ChatViewModel", "UseCase success: ${chatResult.message.content}")
                    _uiState.update { 
                        it.copy(
                            messages = it.messages + chatResult.message,
                            isLoading = false,
                            conversationId = chatResult.conversationId
                        ) 
                    }
                    // Save conversation locally after each response
                    saveConversationLocally()
                }.onFailure { error ->
                    android.util.Log.e("ChatViewModel", "UseCase failure: ${error.message}", error)
                    _uiState.update { it.copy(isLoading = false, error = error.localizedMessage) }
                    _uiEvent.send(error.localizedMessage ?: "Unknown error")
                }
            }
        }
    }

    private fun detectIfCode(text: String): Boolean {
        // Simple heuristics to detect Kotlin code
        val codeIndicators = listOf(
            "fun ", "class ", "val ", "var ", "import ", "package ",
            "{", "}", "(", ")", "=", "->", ":", "//", "/*"
        )
        
        // If text contains multiple code indicators, it's likely code
        val indicatorCount = codeIndicators.count { text.contains(it) }
        
        // Also check if it's multi-line (code is usually multi-line)
        val isMultiLine = text.contains("\n")
        
        return indicatorCount >= 3 || (isMultiLine && indicatorCount >= 2)
    }
    
    private suspend fun saveConversationLocally() {
        val currentState = _uiState.value
        val entity = currentState.toConversationEntity()
        
        if (entity != null) {
            conversationDao.insertConversation(entity)
            android.util.Log.d("ChatViewModel", "Saved conversation ${currentState.conversationId} locally")
        }
    }
    
    suspend fun loadConversation(conversationId: String) {
        val entity = conversationDao.getConversation(conversationId)
        if (entity != null) {
            val messages = entity.toUiMessages()
            _uiState.update {
                it.copy(
                    conversationId = entity.id,
                    messages = messages
                )
            }
            android.util.Log.d("ChatViewModel", "Loaded conversation $conversationId from local storage")
        }
    }
}

