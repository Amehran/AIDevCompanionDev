package com.aidevcompanion.app.domain.usecase

import com.aidevcompanion.app.domain.repository.ChatRepository
import io.mockk.coEvery
import io.mockk.coVerify
import io.mockk.mockk
import kotlinx.coroutines.test.runTest
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class CheckHealthUseCaseTest {

    private val repository: ChatRepository = mockk()
    private val checkHealthUseCase = CheckHealthUseCase(repository)

    @Test
    fun `invoke returns true when repository returns true`() = runTest {
        // Given
        coEvery { repository.checkHealth() } returns true

        // When
        val result = checkHealthUseCase()

        // Then
        assertTrue(result)
        coVerify(exactly = 1) { repository.checkHealth() }
    }

    @Test
    fun `invoke returns false when repository returns false`() = runTest {
        // Given
        coEvery { repository.checkHealth() } returns false

        // When
        val result = checkHealthUseCase()

        // Then
        assertFalse(result)
        coVerify(exactly = 1) { repository.checkHealth() }
    }
}
