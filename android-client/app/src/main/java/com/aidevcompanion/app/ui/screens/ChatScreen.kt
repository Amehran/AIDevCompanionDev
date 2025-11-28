package com.aidevcompanion.app.ui.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.lazy.rememberLazyListState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Send
import androidx.compose.material.icons.filled.Code
import androidx.compose.material.icons.filled.ShortText
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.unit.dp
import com.aidevcompanion.app.ui.viewmodel.ChatUiState
import com.aidevcompanion.app.domain.model.ChatMessage
import dev.jeziellago.compose.markdowntext.MarkdownText

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ChatScreen(
    uiState: ChatUiState,
    onSendMessage: (String, Boolean) -> Unit
) {
    var textInput by remember { mutableStateOf("") }
    val listState = rememberLazyListState()

    LaunchedEffect(uiState.messages.size) {
        if (uiState.messages.isNotEmpty()) {
            listState.animateScrollToItem(uiState.messages.size - 1)
        }
    }

    Scaffold(
        bottomBar = {
            ChatInputBar(
                text = textInput,
                onTextChange = { textInput = it },
                onSend = { isCode ->
                    if (textInput.isNotBlank()) {
                        onSendMessage(textInput, isCode)
                        textInput = ""
                    }
                },
                isLoading = uiState.isLoading
            )
        }
    ) { paddingValues ->
        LazyColumn(
            state = listState,
            modifier = Modifier
                .fillMaxSize()
                .padding(paddingValues)
                .padding(horizontal = 16.dp),
            verticalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            items(uiState.messages) { message ->
                ChatBubble(message)
            }
            if (uiState.isLoading) {
                item {
                    CircularProgressIndicator(modifier = Modifier.size(24.dp))
                }
            }
        }
    }
}

@Composable
fun ChatBubble(message: ChatMessage) {
    val alignment = if (message.isUser) Alignment.End else Alignment.Start
    val backgroundColor = if (message.isUser) 
        MaterialTheme.colorScheme.primaryContainer 
    else 
        MaterialTheme.colorScheme.secondaryContainer

    Column(
        modifier = Modifier.fillMaxWidth(),
        horizontalAlignment = alignment
    ) {
        Box(
            modifier = Modifier
                .clip(RoundedCornerShape(12.dp))
                .background(backgroundColor)
                .padding(12.dp)
        ) {
            if (message.isCode) {
                Text(
                    text = message.content,
                    fontFamily = FontFamily.Monospace,
                    color = MaterialTheme.colorScheme.onPrimaryContainer
                )
            } else {
                if (message.isUser) {
                    Text(text = message.content)
                } else {
                    MarkdownText(markdown = message.content)
                }
            }
        }
    }
}

@Composable
fun ChatInputBar(
    text: String,
    onTextChange: (String) -> Unit,
    onSend: (Boolean) -> Unit, // Changed to accept isCode boolean
    isLoading: Boolean
) {
    var isCodeMode by remember { mutableStateOf(false) }

    Column(modifier = Modifier.fillMaxWidth()) {
import androidx.compose.material.icons.filled.Code
import androidx.compose.material.icons.filled.ShortText
// ...

        if (isCodeMode) {
            Text(
                text = "Code Mode Active",
                style = MaterialTheme.typography.labelSmall,
                color = MaterialTheme.colorScheme.primary,
                modifier = Modifier.padding(horizontal = 16.dp, vertical = 4.dp)
            )
        }
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(8.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            IconButton(onClick = { isCodeMode = !isCodeMode }) {
                Icon(
                    imageVector = if (isCodeMode) Icons.Default.Code else Icons.Default.ShortText,
                    contentDescription = if (isCodeMode) "Switch to Text" else "Switch to Code",
                    tint = if (isCodeMode) MaterialTheme.colorScheme.primary else MaterialTheme.colorScheme.onSurface
                )
            }
            
            TextField(
                value = text,
                onValueChange = onTextChange,
                modifier = Modifier.weight(1f),
                placeholder = { Text(if (isCodeMode) "Paste your code here..." else "Type a message...") },
                maxLines = 4,
                colors = TextFieldDefaults.colors(
                    focusedContainerColor = if (isCodeMode) MaterialTheme.colorScheme.surfaceVariant else MaterialTheme.colorScheme.surface,
                    unfocusedContainerColor = if (isCodeMode) MaterialTheme.colorScheme.surfaceVariant else MaterialTheme.colorScheme.surface
                )
            )
            Spacer(modifier = Modifier.width(8.dp))
            IconButton(
                onClick = { onSend(isCodeMode) },
                enabled = !isLoading && text.isNotBlank()
            ) {
                Icon(Icons.Default.Send, contentDescription = "Send")
            }
        }
    }
}
