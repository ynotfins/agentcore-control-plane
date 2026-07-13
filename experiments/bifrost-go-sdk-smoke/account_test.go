package main

import (
	"context"
	"errors"
	"os"
	"strings"
	"testing"
	"time"

	"github.com/maximhq/bifrost/core/schemas"
)

func TestGetConfiguredProviders(t *testing.T) {
	t.Parallel()
	account := NewOpenAIAccountForTest()
	providers, err := account.GetConfiguredProviders()
	if err != nil {
		t.Fatalf("GetConfiguredProviders: %v", err)
	}
	if len(providers) != 1 || providers[0] != schemas.OpenAI {
		t.Fatalf("expected [openai], got %#v", providers)
	}
}

func TestGetKeysForProviderOpenAI(t *testing.T) {
	t.Setenv(openaiAPIKeyEnv, "sk-test-not-a-real-key")
	account := NewOpenAIAccountForTest()
	keys, err := account.GetKeysForProvider(context.Background(), schemas.OpenAI)
	if err != nil {
		t.Fatalf("GetKeysForProvider: %v", err)
	}
	if len(keys) != 1 {
		t.Fatalf("expected 1 key, got %d", len(keys))
	}
	if keys[0].ID != smokeKeyID || keys[0].Name != smokeKeyName {
		t.Fatalf("unexpected key identity: id=%q name=%q", keys[0].ID, keys[0].Name)
	}
	if keys[0].Weight != 1.0 {
		t.Fatalf("expected weight 1.0, got %v", keys[0].Weight)
	}
	if !keys[0].Models.IsUnrestricted() {
		t.Fatalf("expected unrestricted models whitelist")
	}
	if !keys[0].Value.IsFromEnv() {
		t.Fatalf("expected env-backed SecretVar")
	}
	if keys[0].Value.EnvKey() != openaiAPIKeyEnv {
		t.Fatalf("expected env key %s, got %s", openaiAPIKeyEnv, keys[0].Value.EnvKey())
	}
	// Ensure we never accidentally stringify the secret into test names/logs via %#v of Value.Val.
	if strings.Contains(keys[0].Value.GetRawRef(), "sk-") {
		t.Fatalf("raw ref unexpectedly contains key material")
	}
}

func TestGetKeysForProviderUnsupported(t *testing.T) {
	t.Setenv(openaiAPIKeyEnv, "sk-test-not-a-real-key")
	account := NewOpenAIAccountForTest()
	_, err := account.GetKeysForProvider(context.Background(), schemas.Anthropic)
	if !errors.Is(err, ErrProviderNotSupported) {
		t.Fatalf("expected ErrProviderNotSupported, got %v", err)
	}
}

func TestMissingOpenAIAPIKey(t *testing.T) {
	t.Setenv(openaiAPIKeyEnv, "")
	_, err := NewOpenAIAccountFromEnv()
	if !errors.Is(err, ErrMissingOpenAIAPIKey) {
		t.Fatalf("expected ErrMissingOpenAIAPIKey, got %v", err)
	}

	account := NewOpenAIAccountForTest()
	_, err = account.GetKeysForProvider(context.Background(), schemas.OpenAI)
	if !errors.Is(err, ErrMissingOpenAIAPIKey) {
		t.Fatalf("expected ErrMissingOpenAIAPIKey from GetKeysForProvider, got %v", err)
	}
}

func TestGetConfigForProvider(t *testing.T) {
	t.Parallel()
	account := NewOpenAIAccountForTest()
	cfg, err := account.GetConfigForProvider(schemas.OpenAI)
	if err != nil {
		t.Fatalf("GetConfigForProvider: %v", err)
	}
	if cfg.NetworkConfig.DefaultRequestTimeoutInSeconds != 60 {
		t.Fatalf("unexpected timeout: %d", cfg.NetworkConfig.DefaultRequestTimeoutInSeconds)
	}
	if cfg.NetworkConfig.MaxRetries != 2 {
		t.Fatalf("unexpected max retries: %d", cfg.NetworkConfig.MaxRetries)
	}
	if cfg.ConcurrencyAndBufferSize.Concurrency != 4 || cfg.ConcurrencyAndBufferSize.BufferSize != 16 {
		t.Fatalf("unexpected concurrency/buffer: %+v", cfg.ConcurrencyAndBufferSize)
	}

	_, err = account.GetConfigForProvider(schemas.Anthropic)
	if !errors.Is(err, ErrProviderNotSupported) {
		t.Fatalf("expected ErrProviderNotSupported, got %v", err)
	}
}

func TestValidateChatResponseShape(t *testing.T) {
	t.Parallel()
	good := &schemas.BifrostChatResponse{
		Model: smokeModel,
		Choices: []schemas.BifrostResponseChoice{{
			ChatNonStreamResponseChoice: &schemas.ChatNonStreamResponseChoice{
				Message: &schemas.ChatMessage{
					Role: schemas.ChatMessageRoleAssistant,
					Content: &schemas.ChatMessageContent{
						ContentStr: schemas.Ptr("PONG"),
					},
				},
			},
		}},
		Usage: &schemas.BifrostLLMUsage{
			PromptTokens:     10,
			CompletionTokens: 1,
			TotalTokens:      11,
		},
		ExtraFields: schemas.BifrostResponseExtraFields{
			Provider: schemas.OpenAI,
			Latency:  42,
		},
	}
	if err := ValidateChatResponseShape(good); err != nil {
		t.Fatalf("expected valid shape: %v", err)
	}
	meta := MetaFromChatResponse(good, "req-test")
	if !meta.OK || meta.ContentChars != 4 || meta.TotalTokens != 11 || meta.LatencyMS != 42 {
		t.Fatalf("unexpected meta: %+v", meta)
	}
	line := FormatSmokeMeta(meta)
	if strings.Contains(line, "PONG") {
		t.Fatalf("formatted meta unexpectedly contains response content")
	}

	badCases := []*schemas.BifrostChatResponse{
		nil,
		{},
		{Choices: []schemas.BifrostResponseChoice{{}}},
		{Choices: []schemas.BifrostResponseChoice{{
			ChatNonStreamResponseChoice: &schemas.ChatNonStreamResponseChoice{
				Message: &schemas.ChatMessage{Content: &schemas.ChatMessageContent{ContentStr: schemas.Ptr("  ")}},
			},
		}}},
	}
	for i, bad := range badCases {
		if err := ValidateChatResponseShape(bad); err == nil {
			t.Fatalf("case %d: expected validation error", i)
		}
	}
}

func TestRequestContextTimeout(t *testing.T) {
	t.Parallel()
	bfCtx, cancel := newRequestContext(context.Background(), "timeout-test", 5*time.Millisecond)
	defer cancel()
	time.Sleep(20 * time.Millisecond)
	if err := bfCtx.Err(); !errors.Is(err, context.DeadlineExceeded) {
		t.Fatalf("expected deadline exceeded, got %v", err)
	}
	if got, _ := bfCtx.Value(schemas.BifrostContextKeyRequestID).(string); got != "timeout-test" {
		t.Fatalf("request id not set: %q", got)
	}
}

func TestRetryPolicyDoesNotEnableTools(t *testing.T) {
	t.Parallel()
	// Guardrail: retries are only safe here because this POC never configures MCP/tools.
	// If tools are added later, MaxRetries must be revisited for non-idempotent operations.
	account := NewOpenAIAccountForTest()
	cfg, err := account.GetConfigForProvider(schemas.OpenAI)
	if err != nil {
		t.Fatal(err)
	}
	if cfg.NetworkConfig.MaxRetries < 1 {
		t.Fatalf("expected retries enabled for transient failures")
	}
	providers, _ := account.GetConfiguredProviders()
	if len(providers) != 1 {
		t.Fatalf("fallback chains require multiple providers; keep single-provider until credentials exist")
	}
}

func TestRequireOpenAIAPIKeyUsesProcessEnv(t *testing.T) {
	orig, had := os.LookupEnv(openaiAPIKeyEnv)
	t.Cleanup(func() {
		if had {
			_ = os.Setenv(openaiAPIKeyEnv, orig)
		} else {
			_ = os.Unsetenv(openaiAPIKeyEnv)
		}
	})
	_ = os.Unsetenv(openaiAPIKeyEnv)
	if err := requireOpenAIAPIKey(); !errors.Is(err, ErrMissingOpenAIAPIKey) {
		t.Fatalf("expected missing key error, got %v", err)
	}
}
