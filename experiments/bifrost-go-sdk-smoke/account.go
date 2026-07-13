package main

import (
	"context"
	"errors"
	"fmt"
	"os"
	"strings"
	"time"

	"github.com/maximhq/bifrost/core/schemas"
)

const (
	openaiAPIKeyEnv = "OPENAI_API_KEY"
	smokeModel      = "gpt-4o-mini"
	smokeKeyID      = "openai-smoke-1"
	smokeKeyName    = "openai-smoke"
)

// ErrMissingOpenAIAPIKey is returned when OPENAI_API_KEY is absent or blank.
var ErrMissingOpenAIAPIKey = errors.New("OPENAI_API_KEY is not set or empty")

// ErrProviderNotSupported is returned for providers this Account does not configure.
var ErrProviderNotSupported = errors.New("provider not supported")

// OpenAIAccount implements schemas.Account for a single OpenAI provider/key.
// It is intentionally narrow: this POC is model routing via the Go SDK, not an MCP gateway.
type OpenAIAccount struct {
	keyID   string
	keyName string
}

// Compile-time check that OpenAIAccount satisfies schemas.Account for bifrost/core@v1.7.0.
var _ schemas.Account = (*OpenAIAccount)(nil)

// NewOpenAIAccountFromEnv validates that OPENAI_API_KEY is present and non-empty,
// then returns an Account that resolves the key via Bifrost's env SecretVar ref
// (so the secret is not stored in this struct).
func NewOpenAIAccountFromEnv() (*OpenAIAccount, error) {
	if err := requireOpenAIAPIKey(); err != nil {
		return nil, err
	}
	return &OpenAIAccount{
		keyID:   smokeKeyID,
		keyName: smokeKeyName,
	}, nil
}

// NewOpenAIAccountForTest builds an Account without reading the live environment.
// Used by unit tests that inject a temporary OPENAI_API_KEY value.
func NewOpenAIAccountForTest() *OpenAIAccount {
	return &OpenAIAccount{
		keyID:   smokeKeyID,
		keyName: smokeKeyName,
	}
}

func requireOpenAIAPIKey() error {
	if strings.TrimSpace(os.Getenv(openaiAPIKeyEnv)) == "" {
		return ErrMissingOpenAIAPIKey
	}
	return nil
}

// GetConfiguredProviders returns the single verified provider (OpenAI).
func (a *OpenAIAccount) GetConfiguredProviders() ([]schemas.ModelProvider, error) {
	return []schemas.ModelProvider{schemas.OpenAI}, nil
}

// GetKeysForProvider returns the OpenAI key resolved from env.OPENAI_API_KEY.
// Signature matches bifrost/core@v1.7.0 (context.Context, not *context.Context).
func (a *OpenAIAccount) GetKeysForProvider(ctx context.Context, provider schemas.ModelProvider) ([]schemas.Key, error) {
	_ = ctx
	if provider != schemas.OpenAI {
		return nil, fmt.Errorf("%w: %s", ErrProviderNotSupported, provider)
	}
	if err := requireOpenAIAPIKey(); err != nil {
		return nil, err
	}

	return []schemas.Key{{
		ID:     a.keyID,
		Name:   a.keyName,
		Value:  *schemas.NewSecretVar("env." + openaiAPIKeyEnv),
		Models: schemas.WhiteList{"*"},
		Weight: 1.0,
	}}, nil
}

// GetConfigForProvider returns network, retry, and concurrency settings for OpenAI.
//
// Retries: MaxRetries=2 only covers transient network/5xx failures for the same
// single key. No tools/MCP clients are configured in this POC, so retries cannot
// duplicate non-idempotent tool side effects. Fallbacks are omitted because only
// one provider credential is available.
func (a *OpenAIAccount) GetConfigForProvider(provider schemas.ModelProvider) (*schemas.ProviderConfig, error) {
	if provider != schemas.OpenAI {
		return nil, fmt.Errorf("%w: %s", ErrProviderNotSupported, provider)
	}

	net := schemas.DefaultNetworkConfig
	net.DefaultRequestTimeoutInSeconds = 60
	net.MaxRetries = 2
	net.RetryBackoffInitial = 500 * time.Millisecond
	net.RetryBackoffMax = 5 * time.Second

	return &schemas.ProviderConfig{
		NetworkConfig: net,
		ConcurrencyAndBufferSize: schemas.ConcurrencyAndBufferSize{
			// POC-sized pool; SDK defaults are 1000/5000 which are overkill here.
			Concurrency: 4,
			BufferSize:  16,
		},
	}, nil
}
