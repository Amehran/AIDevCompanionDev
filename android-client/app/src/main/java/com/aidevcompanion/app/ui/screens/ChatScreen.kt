package com.aidevcompanion.app.ui.screens

import androidx.compose.animation.AnimatedVisibility
import androidx.compose.animation.fadeIn
import androidx.compose.animation.fadeOut
import androidx.compose.animation.slideInVertically
import androidx.compose.animation.slideOutVertically
import androidx.compose.foundation.background
import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.lazy.rememberLazyListState
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Send
import androidx.compose.material.icons.filled.Settings
import androidx.compose.material.icons.filled.Info
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.draw.scale
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.animation.core.*
import kotlinx.coroutines.delay
import com.aidevcompanion.app.ui.viewmodel.ChatUiState
import com.aidevcompanion.app.domain.model.ChatMessage
import dev.jeziellago.compose.markdowntext.MarkdownText

@OptIn(ExperimentalMaterial3Api::class, androidx.compose.foundation.ExperimentalFoundationApi::class)
@Composable
fun ChatScreen(
    uiState: ChatUiState,
    uiEvent: kotlinx.coroutines.flow.Flow<String>,
    onSendMessage: (String) -> Unit
) {
    var textInput by remember { mutableStateOf("") }
    val listState = rememberLazyListState()

    LaunchedEffect(uiState.messages.size) {
        if (uiState.messages.isNotEmpty()) {
            listState.animateScrollToItem(uiState.messages.size - 1)
        }
    }

    val snackbarHostState = remember { SnackbarHostState() }

    LaunchedEffect(true) {
        uiEvent.collect { error ->
            snackbarHostState.showSnackbar(
                message = error,
                duration = SnackbarDuration.Long
            )
        }
    }

    Scaffold(
        snackbarHost = { 
            SnackbarHost(snackbarHostState) { data ->
                Snackbar(
                    snackbarData = data,
                    containerColor = MaterialTheme.colorScheme.errorContainer,
                    contentColor = MaterialTheme.colorScheme.onErrorContainer
                )
            }
        },
        topBar = {
            TopAppBar(
                title = { 
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Icon(
                            Icons.Default.Info,
                            contentDescription = null,
                            tint = MaterialTheme.colorScheme.primary
                        )
                        Spacer(Modifier.width(8.dp))
                        Text("AI Code Assistant", fontWeight = FontWeight.Bold)
                    }
                },
                colors = TopAppBarDefaults.topAppBarColors(
                    containerColor = MaterialTheme.colorScheme.surface
                )
            )
        },
        bottomBar = {
            ChatInputBar(
                text = textInput,
                onTextChange = { textInput = it },
                onSend = {
                    if (textInput.isNotBlank()) {
                        onSendMessage(textInput)
                        textInput = ""
                    }
                },
                isLoading = uiState.isLoading
            )
        }
    ) { paddingValues ->
        Box(
            modifier = Modifier
                .fillMaxSize()
                .padding(paddingValues)
        ) {
            if (uiState.messages.isEmpty()) {
                EmptyState()
            } else {
                LazyColumn(
                    state = listState,
                    modifier = Modifier.fillMaxSize().testTag("message_list"),
                    contentPadding = PaddingValues(16.dp),
                    verticalArrangement = Arrangement.spacedBy(16.dp)
                ) {
                    items(
                        items = uiState.messages,
                        key = { it.id }
                    ) { message ->
                        AnimatedVisibility(
                            visible = true,
                            enter = fadeIn() + slideInVertically(),
                            modifier = Modifier.animateItemPlacement()
                        ) {
                            ChatBubble(
                                message = message,
                                onActionClick = { action -> onSendMessage(action) }
                            )
                        }
                    }
                    if (uiState.isLoading) {
                        item {
                            TypingIndicator(
                                modifier = Modifier.padding(start = 16.dp, top = 8.dp).testTag("typing_indicator")
                            )
                        }
                    }
                }
            }
        }
    }
}

@Composable
fun EmptyState() {
    Column(
        modifier = Modifier.fillMaxSize().testTag("empty_state"),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.Center
    ) {
        Icon(
            Icons.Default.Settings,
            contentDescription = null,
            modifier = Modifier.size(80.dp),
            tint = MaterialTheme.colorScheme.primary.copy(alpha = 0.3f)
        )
        Spacer(Modifier.height(16.dp))
        Text(
            "Paste Kotlin code to get started",
            style = MaterialTheme.typography.titleMedium,
            color = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.6f)
        )
        Spacer(Modifier.height(8.dp))
        Text(
            "I'll analyze it for issues and suggest improvements",
            style = MaterialTheme.typography.bodyMedium,
            color = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.4f)
        )
    }
}

@Composable
fun TypingIndicator(
    modifier: Modifier = Modifier,
    dotSize: androidx.compose.ui.unit.Dp = 10.dp,
    dotColor: Color = MaterialTheme.colorScheme.primary,
    animationDelay: Int = 400
) {
    val circles = listOf(
        remember { Animatable(initialValue = 0f) },
        remember { Animatable(initialValue = 0f) },
        remember { Animatable(initialValue = 0f) }
    )

    circles.forEachIndexed { index, animatable ->
        LaunchedEffect(Unit) {
            delay(index * (animationDelay / 3).toLong())
            animatable.animateTo(
                targetValue = 1f,
                animationSpec = infiniteRepeatable(
                    animation = tween(durationMillis = animationDelay, easing = LinearEasing),
                    repeatMode = RepeatMode.Reverse
                )
            )
        }
    }

    Row(
        modifier = modifier,
        horizontalArrangement = Arrangement.spacedBy(6.dp),
        verticalAlignment = Alignment.CenterVertically
    ) {
        circles.forEach { animatable ->
            Box(
                modifier = Modifier
                    .size(dotSize)
                    .scale(scale = 0.5f + (animatable.value * 0.5f))
                    .background(color = dotColor, shape = CircleShape)
            )
        }
    }
}

@Composable
fun ChatBubble(
    message: ChatMessage,
    onActionClick: (String) -> Unit
) {
    val isUser = message.isUser
    val alignment = if (isUser) Alignment.End else Alignment.Start
    
    val backgroundColor = if (isUser) 
        MaterialTheme.colorScheme.primaryContainer 
    else 
        MaterialTheme.colorScheme.surfaceVariant

    val contentColor = if (isUser) 
        MaterialTheme.colorScheme.onPrimaryContainer 
    else 
        MaterialTheme.colorScheme.onSurfaceVariant

    val shape = if (isUser) 
        RoundedCornerShape(20.dp, 20.dp, 4.dp, 20.dp)
    else 
        RoundedCornerShape(20.dp, 20.dp, 20.dp, 4.dp)

    Column(
        modifier = Modifier.fillMaxWidth(),
        horizontalAlignment = alignment
    ) {
        // Label
        if (!isUser) {
            Row(
                verticalAlignment = Alignment.CenterVertically,
                modifier = Modifier.padding(start = 12.dp, bottom = 4.dp)
            ) {
                Icon(
                    Icons.Default.Info,
                    contentDescription = null,
                    modifier = Modifier.size(16.dp),
                    tint = MaterialTheme.colorScheme.primary
                )
                Spacer(Modifier.width(4.dp))
                Text(
                    text = "AI Assistant",
                    style = MaterialTheme.typography.labelSmall,
                    color = MaterialTheme.colorScheme.primary,
                    fontWeight = FontWeight.SemiBold
                )
            }
        }

        // Message bubble
        Surface(
            modifier = Modifier.widthIn(max = 320.dp),
            shape = shape,
            color = backgroundColor,
            shadowElevation = if (isUser) 0.dp else 1.dp
        ) {
            Column(modifier = Modifier.padding(16.dp)) {
                if (message.isCode) {
                    Surface(
                        shape = RoundedCornerShape(8.dp),
                        color = MaterialTheme.colorScheme.surface.copy(alpha = 0.5f)
                    ) {
                        Column(modifier = Modifier.padding(12.dp)) {
                            Row(
                                verticalAlignment = Alignment.CenterVertically,
                                modifier = Modifier.padding(bottom = 8.dp)
                            ) {
                                Icon(
                                    Icons.Default.Settings,
                                    contentDescription = null,
                                    modifier = Modifier.size(14.dp),
                                    tint = contentColor.copy(alpha = 0.7f)
                                )
                                Spacer(Modifier.width(4.dp))
                                Text(
                                    text = "CODE",
                                    style = MaterialTheme.typography.labelSmall,
                                    color = contentColor.copy(alpha = 0.7f),
                                    fontWeight = FontWeight.Bold
                                )
                            }
                            Text(
                                text = message.content,
                                fontFamily = FontFamily.Monospace,
                                color = contentColor,
                                style = MaterialTheme.typography.bodySmall
                            )
                        }
                    }
                } else {
                    if (isUser) {
                        Text(
                            text = message.content,
                            color = contentColor,
                            style = MaterialTheme.typography.bodyMedium
                        )
                    } else {
                        Box(modifier = Modifier.testTag("markdown_text")) {
                            MarkdownText(
                                markdown = message.content,
                                color = contentColor,
                                style = MaterialTheme.typography.bodyMedium
                            )
                        }
                    }
                }
            }
        }

        // Suggested Actions
        if (!isUser && !message.suggestedActions.isNullOrEmpty()) {
            Spacer(Modifier.height(8.dp))
            Row(
                modifier = Modifier
                    .horizontalScroll(rememberScrollState())
                    .padding(start = 12.dp),
                horizontalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                message.suggestedActions.forEach { action ->
                    SuggestionChip(
                        onClick = { onActionClick(action) },
                        label = { 
                            Text(
                                action,
                                style = MaterialTheme.typography.labelMedium
                            ) 
                        },
                        colors = SuggestionChipDefaults.suggestionChipColors(
                            containerColor = MaterialTheme.colorScheme.primary.copy(alpha = 0.1f),
                            labelColor = MaterialTheme.colorScheme.primary
                        ),
                        border = SuggestionChipDefaults.suggestionChipBorder(
                            borderColor = MaterialTheme.colorScheme.primary.copy(alpha = 0.3f)
                        )
                    )
                }
            }
        }
    }
}

@Composable
fun ChatInputBar(
    text: String,
    onTextChange: (String) -> Unit,
    onSend: () -> Unit,
    isLoading: Boolean
) {
    Surface(
        shadowElevation = 8.dp,
        color = MaterialTheme.colorScheme.surface
    ) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(12.dp),
            verticalAlignment = Alignment.Bottom
        ) {
            OutlinedTextField(
                value = text,
                onValueChange = onTextChange,
                modifier = Modifier.weight(1f).testTag("chat_input"),
                placeholder = { 
                    Text(
                        "Ask a question or paste code...",
                        style = MaterialTheme.typography.bodyMedium
                    ) 
                },
                maxLines = 6,
                shape = RoundedCornerShape(24.dp),
                colors = OutlinedTextFieldDefaults.colors(
                    focusedBorderColor = MaterialTheme.colorScheme.primary,
                    unfocusedBorderColor = MaterialTheme.colorScheme.outline.copy(alpha = 0.3f)
                )
            )
            Spacer(modifier = Modifier.width(8.dp))
            FloatingActionButton(
                onClick = onSend,
                modifier = Modifier.size(56.dp).testTag("send_button"),
                containerColor = MaterialTheme.colorScheme.primary,
                elevation = FloatingActionButtonDefaults.elevation(
                    defaultElevation = 0.dp,
                    pressedElevation = 2.dp
                )
            ) {
                if (isLoading) {
                    CircularProgressIndicator(
                        modifier = Modifier.size(24.dp).testTag("loading_indicator"),
                        color = MaterialTheme.colorScheme.onPrimary,
                        strokeWidth = 2.dp
                    )
                } else {
                    Icon(
                        Icons.Default.Send,
                        contentDescription = "Send",
                        tint = MaterialTheme.colorScheme.onPrimary
                    )
                }
            }
        }
    }
}
