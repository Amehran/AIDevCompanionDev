package com.aidevcompanion.app

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.rememberNavController
import com.aidevcompanion.app.ui.screens.ChatScreen
import com.aidevcompanion.app.ui.screens.IntroScreen
import com.aidevcompanion.app.ui.viewmodel.ChatViewModel
import dagger.hilt.android.AndroidEntryPoint

@AndroidEntryPoint
class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            MaterialTheme {
                Surface(
                    modifier = Modifier.fillMaxSize(),
                    color = MaterialTheme.colorScheme.background
                ) {
                    val navController = rememberNavController()
                    val viewModel: ChatViewModel = hiltViewModel()
                    val uiState by viewModel.uiState.collectAsState()

                    NavHost(navController = navController, startDestination = "intro") {
                        composable("intro") {
                            IntroScreen(
                                uiState = uiState,
                                onRetry = { viewModel.checkConnection() },
                                onStartChat = { navController.navigate("chat") }
                            )
                        }
                        composable("chat") {
                            ChatScreen(
                                uiState = uiState,
                                uiEvent = viewModel.uiEvent,
                                onSendMessage = { text -> 
                                    viewModel.sendMessage(text) 
                                }
                            )
                        }
                    }
                }
            }
        }
    }
}
