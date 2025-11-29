package com.aidevcompanion.app.ui.screens

import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createComposeRule
import com.aidevcompanion.app.domain.model.ChatMessage
import com.aidevcompanion.app.ui.viewmodel.ChatUiState
import kotlinx.coroutines.flow.flowOf
import org.junit.Rule
import org.junit.Test

class ChatScreenTest {

    @get:Rule
    val composeTestRule = createComposeRule()

    @Test
    fun emptyState_isDisplayed_whenNoMessages() {
        composeTestRule.setContent {
            ChatScreen(
                uiState = ChatUiState(messages = emptyList()),
                uiEvent = flowOf(),
                onSendMessage = {}
            )
        }

        composeTestRule.onNodeWithTag("empty_state").assertIsDisplayed()
        composeTestRule.onNodeWithText("Paste Kotlin code to get started").assertIsDisplayed()
    }

    @Test
    fun messages_areDisplayed_whenListIsNotEmpty() {
        val messages = listOf(
            ChatMessage(id = "1", content = "Hello AI", isUser = true),
            ChatMessage(id = "2", content = "Hello User", isUser = false)
        )

        composeTestRule.setContent {
            ChatScreen(
                uiState = ChatUiState(messages = messages),
                uiEvent = flowOf(),
                onSendMessage = {}
            )
        }

        composeTestRule.onNodeWithTag("message_list").assertIsDisplayed()
        composeTestRule.onNodeWithText("Hello AI").assertIsDisplayed()
        composeTestRule.onNodeWithText("Hello User").assertIsDisplayed()
        composeTestRule.onNodeWithTag("empty_state").assertDoesNotExist()
    }

    @Test
    fun typingIndicator_isDisplayed_whenLoading() {
        composeTestRule.setContent {
            ChatScreen(
                uiState = ChatUiState(isLoading = true, messages = listOf(ChatMessage(content = "Hi", isUser = true))),
                uiEvent = flowOf(),
                onSendMessage = {}
            )
        }

        composeTestRule.onNodeWithTag("loading_indicator").assertIsDisplayed()
        // Also the typing indicator in the list
        composeTestRule.onNodeWithTag("typing_indicator").assertIsDisplayed()
    }

    @Test
    fun sendMessage_invokesCallback() {
        var sentMessage = ""
        composeTestRule.setContent {
            ChatScreen(
                uiState = ChatUiState(),
                uiEvent = flowOf(),
                onSendMessage = { sentMessage = it }
            )
        }

        composeTestRule.onNodeWithTag("chat_input").performTextInput("Analyze this code")
        composeTestRule.onNodeWithTag("send_button").performClick()

        assert(sentMessage == "Analyze this code")
    }
}
