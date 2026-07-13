package main

import (
	"context"
	"fmt"
	"log"
	"time"

	bifrost "github.com/maximhq/bifrost/core"
	"github.com/maximhq/bifrost/core/schemas"
)

const (
	defaultRequestTimeout = 45 * time.Second
	smokePromptMarker     = "Reply with exactly the word PONG and nothing else."
)

// bifrostError wraps schemas.BifrostError as a Go error without leaking secrets.
func bifrostError(err *schemas.BifrostError) error {
	if err == nil {
		return nil
	}
	msg := "bifrost request failed"
	if err.Error != nil && err.Error.Message != "" {
		msg = err.Error.Message
	}
	if err.StatusCode != nil {
		return fmt.Errorf("%s (status=%d)", msg, *err.StatusCode)
	}
	return fmt.Errorf("%s", msg)
}

// newClient initializes Bifrost with the OpenAI Account.
func newClient(ctx context.Context, account schemas.Account) (*bifrost.Bifrost, error) {
	client, err := bifrost.Init(ctx, schemas.BifrostConfig{
		Account: account,
		Logger:  bifrost.NewDefaultLogger(schemas.LogLevelError),
	})
	if err != nil {
		return nil, fmt.Errorf("bifrost init: %w", err)
	}
	return client, nil
}

func chatMessages() []schemas.ChatMessage {
	return []schemas.ChatMessage{{
		Role: schemas.ChatMessageRoleUser,
		Content: &schemas.ChatMessageContent{
			ContentStr: schemas.Ptr(smokePromptMarker),
		},
	}}
}

func newRequestContext(parent context.Context, requestID string, timeout time.Duration) (*schemas.BifrostContext, context.CancelFunc) {
	if timeout <= 0 {
		timeout = defaultRequestTimeout
	}
	ctx, cancel := context.WithTimeout(parent, timeout)
	bfCtx := schemas.NewBifrostContext(ctx, schemas.NoDeadline)
	bfCtx.SetValue(schemas.BifrostContextKeyRequestID, requestID)
	bfCtx.SetValue(schemas.BifrostContextKeyExtraHeaders, map[string][]string{
		"x-correlation-id": {requestID},
	})
	return bfCtx, cancel
}

// runChatSmoke performs one low-cost chat completion and returns sanitized metadata.
func runChatSmoke(parent context.Context, client *bifrost.Bifrost, requestID string) (SmokeMeta, error) {
	bfCtx, cancel := newRequestContext(parent, requestID, defaultRequestTimeout)
	defer cancel()

	resp, berr := client.ChatCompletionRequest(bfCtx, &schemas.BifrostChatRequest{
		Provider: schemas.OpenAI,
		Model:    smokeModel,
		Input:    chatMessages(),
		Params: &schemas.ChatParameters{
			MaxCompletionTokens: schemas.Ptr(16),
			Temperature:         schemas.Ptr(0.0),
		},
	})
	if berr != nil {
		return SmokeMeta{}, bifrostError(berr)
	}
	if err := ValidateChatResponseShape(resp); err != nil {
		return SmokeMeta{}, err
	}
	return MetaFromChatResponse(resp, requestID), nil
}

// runStreamSmoke validates streaming by counting chunks; does not print content.
func runStreamSmoke(parent context.Context, client *bifrost.Bifrost, requestID string) (SmokeMeta, error) {
	bfCtx, cancel := newRequestContext(parent, requestID, defaultRequestTimeout)
	defer cancel()

	stream, berr := client.ChatCompletionStreamRequest(bfCtx, &schemas.BifrostChatRequest{
		Provider: schemas.OpenAI,
		Model:    smokeModel,
		Input:    chatMessages(),
		Params: &schemas.ChatParameters{
			MaxCompletionTokens: schemas.Ptr(16),
			Temperature:         schemas.Ptr(0.0),
		},
	})
	if berr != nil {
		return SmokeMeta{}, bifrostError(berr)
	}

	meta := SmokeMeta{
		OK:        true,
		Provider:  string(schemas.OpenAI),
		Model:     smokeModel,
		RequestID: requestID,
	}
	var contentLen int
	for chunk := range stream {
		if chunk.BifrostError != nil {
			return SmokeMeta{}, bifrostError(chunk.BifrostError)
		}
		meta.StreamChunks++
		if chunk.BifrostChatResponse == nil {
			continue
		}
		meta.LatencyMS = chunk.BifrostChatResponse.ExtraFields.Latency
		if chunk.BifrostChatResponse.Usage != nil {
			meta.PromptTokens = chunk.BifrostChatResponse.Usage.PromptTokens
			meta.CompletionToks = chunk.BifrostChatResponse.Usage.CompletionTokens
			meta.TotalTokens = chunk.BifrostChatResponse.Usage.TotalTokens
		}
		if len(chunk.BifrostChatResponse.Choices) == 0 {
			continue
		}
		choice := chunk.BifrostChatResponse.Choices[0]
		if choice.ChatStreamResponseChoice != nil &&
			choice.ChatStreamResponseChoice.Delta != nil &&
			choice.ChatStreamResponseChoice.Delta.Content != nil {
			contentLen += len(*choice.ChatStreamResponseChoice.Delta.Content)
		}
	}
	meta.ContentChars = contentLen
	if meta.StreamChunks == 0 {
		return SmokeMeta{}, fmt.Errorf("stream produced zero chunks")
	}
	if contentLen == 0 {
		return SmokeMeta{}, fmt.Errorf("stream produced no content deltas")
	}
	return meta, nil
}

func shutdownClient(client *bifrost.Bifrost) {
	if client == nil {
		return
	}
	client.Shutdown()
	log.Printf("status=shutdown ok=true")
}
