package com.aidevcompanion.app.ui.viewmodel

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.aidevcompanion.app.domain.model.ChatMessage
import com.aidevcompanion.app.domain.usecase.CheckHealthUseCase
import com.aidevcompanion.app.domain.usecase.SendMessageUseCase
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
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

@HiltViewModel
class ChatViewModel @Inject constructor(
    private val sendMessageUseCase: SendMessageUseCase,
    private val checkHealthUseCase: CheckHealthUseCase
) : ViewModel() {

    private val _uiState = MutableStateFlow(ChatUiState())
    val uiState: StateFlow<ChatUiState> = _uiState.asStateFlow()

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

    fun sendMessage(text: String, isCode: Boolean = false) {
        val userMessage = ChatMessage(content = text, isUser = true, isCode = isCode)
        _uiState.update { 
            it.copy(
                messages = it.messages + userMessage,
                isLoading = true,
                error = null
            ) 
        }

        viewModelScope.launch {
            sendMessageUseCase(
                conversationId = _uiState.value.conversationId,
                message = if (!isCode) text else null,
                sourceCode = if (isCode) text else ""  // Send empty string instead of null
            ).collect { result ->
                result.onSuccess { chatResult ->
                    _uiState.update { 
                        it.copy(
                            messages = it.messages + chatResult.message,
                            isLoading = false,
                            conversationId = chatResult.conversationId
                        ) 
                    }
                }.onFailure { error ->
                    _uiState.update { 
                        it.copy(
                            isLoading = false,
                            error = error.localizedMessage ?: "Unknown error"
                        ) 
                    }
                }
            }
        }
    }
}
