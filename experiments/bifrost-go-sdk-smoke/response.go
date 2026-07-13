package main

import (
	"fmt"
	"strings"

	"github.com/maximhq/bifrost/core/schemas"
)

// SmokeMeta is sanitized live-run metadata (no prompt/response content).
type SmokeMeta struct {
	OK             bool   `json:"ok"`
	Provider       string `json:"provider"`
	Model          string `json:"model"`
	LatencyMS      int64  `json:"latency_ms"`
	PromptTokens   int    `json:"prompt_tokens,omitempty"`
	CompletionToks int    `json:"completion_tokens,omitempty"`
	TotalTokens    int    `json:"total_tokens,omitempty"`
	ContentChars   int    `json:"content_chars"`
	RequestID      string `json:"request_id,omitempty"`
	StreamChunks   int    `json:"stream_chunks,omitempty"`
}

// ExtractChatText returns non-stream assistant text content when present.
func ExtractChatText(resp *schemas.BifrostChatResponse) (string, error) {
	if resp == nil {
		return "", fmt.Errorf("nil chat response")
	}
	if len(resp.Choices) == 0 {
		return "", fmt.Errorf("chat response has no choices")
	}
	choice := resp.Choices[0]
	if choice.ChatNonStreamResponseChoice == nil || choice.ChatNonStreamResponseChoice.Message == nil {
		return "", fmt.Errorf("chat response missing non-stream message choice")
	}
	msg := choice.ChatNonStreamResponseChoice.Message
	if msg.Content == nil || msg.Content.ContentStr == nil {
		return "", fmt.Errorf("chat message missing ContentStr")
	}
	text := strings.TrimSpace(*msg.Content.ContentStr)
	if text == "" {
		return "", fmt.Errorf("chat message ContentStr is empty")
	}
	return text, nil
}

// ValidateChatResponseShape checks structural fields without requiring a live call.
func ValidateChatResponseShape(resp *schemas.BifrostChatResponse) error {
	_, err := ExtractChatText(resp)
	return err
}

// MetaFromChatResponse builds sanitized metadata from a successful response.
func MetaFromChatResponse(resp *schemas.BifrostChatResponse, requestID string) SmokeMeta {
	meta := SmokeMeta{
		OK:        true,
		RequestID: requestID,
	}
	if resp == nil {
		meta.OK = false
		return meta
	}
	meta.Model = resp.Model
	meta.Provider = string(resp.ExtraFields.Provider)
	meta.LatencyMS = resp.ExtraFields.Latency
	if text, err := ExtractChatText(resp); err == nil {
		meta.ContentChars = len(text)
	}
	if resp.Usage != nil {
		meta.PromptTokens = resp.Usage.PromptTokens
		meta.CompletionToks = resp.Usage.CompletionTokens
		meta.TotalTokens = resp.Usage.TotalTokens
	}
	return meta
}

// FormatSmokeMeta renders a single-line status suitable for logs (no secrets/content).
func FormatSmokeMeta(meta SmokeMeta) string {
	return fmt.Sprintf(
		"status=ok provider=%s model=%s latency_ms=%d prompt_tokens=%d completion_tokens=%d total_tokens=%d content_chars=%d request_id=%s stream_chunks=%d",
		meta.Provider,
		meta.Model,
		meta.LatencyMS,
		meta.PromptTokens,
		meta.CompletionToks,
		meta.TotalTokens,
		meta.ContentChars,
		meta.RequestID,
		meta.StreamChunks,
	)
}
