package com.aidevcompanion.app.data.remote

import com.aidevcompanion.app.data.model.ChatRequest
import com.aidevcompanion.app.data.model.ChatResponse
import com.aidevcompanion.app.data.model.HealthResponse
import retrofit2.Response
import retrofit2.http.Body
import retrofit2.http.GET
import retrofit2.http.POST

interface ApiService {
    @GET("health")
    suspend fun checkHealth(): Response<HealthResponse>

    @POST("chat")
    suspend fun chat(@Body request: ChatRequest): Response<ChatResponse>
}
