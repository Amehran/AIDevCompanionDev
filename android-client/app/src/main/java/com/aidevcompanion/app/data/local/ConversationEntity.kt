package com.aidevcompanion.app.data.local

import androidx.room.Entity
import androidx.room.PrimaryKey
import androidx.room.TypeConverter
import androidx.room.TypeConverters
import com.google.gson.Gson
import com.google.gson.reflect.TypeToken

@Entity(tableName = "conversations")
@TypeConverters(Converters::class)
data class ConversationEntity(
    @PrimaryKey
    val id: String,
    val originalCode: String?,
    val detectedIssues: List<IssueEntity>?,
    val messages: List<MessageEntity>,
    val createdAt: Long,
    val updatedAt: Long
)

data class IssueEntity(
    val type: String,
    val description: String,
    val suggestion: String
)

data class MessageEntity(
    val role: String, // "user" or "assistant"
    val content: String,
    val isCode: Boolean = false,
    val timestamp: Long = System.currentTimeMillis()
)

class Converters {
    private val gson = Gson()
    
    @TypeConverter
    fun fromIssueList(value: List<IssueEntity>?): String? {
        return value?.let { gson.toJson(it) }
    }
    
    @TypeConverter
    fun toIssueList(value: String?): List<IssueEntity>? {
        return value?.let {
            val type = object : TypeToken<List<IssueEntity>>() {}.type
            gson.fromJson(it, type)
        }
    }
    
    @TypeConverter
    fun fromMessageList(value: List<MessageEntity>): String {
        return gson.toJson(value)
    }
    
    @TypeConverter
    fun toMessageList(value: String): List<MessageEntity> {
        val type = object : TypeToken<List<MessageEntity>>() {}.type
        return gson.fromJson(value, type)
    }
}
