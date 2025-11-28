package com.aidevcompanion.app.domain.usecase

import com.aidevcompanion.app.domain.repository.ChatRepository
import javax.inject.Inject

class CheckHealthUseCase @Inject constructor(
    private val repository: ChatRepository
) {
    suspend operator fun invoke(): Boolean {
        return repository.checkHealth()
    }
}
