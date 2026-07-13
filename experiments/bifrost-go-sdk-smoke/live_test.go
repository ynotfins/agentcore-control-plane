//go:build live

package main

import (
	"context"
	"testing"
	"time"

	"github.com/google/uuid"
)

// Live smoke: go test -tags=live -count=1 -run TestLiveSmoke ./...
// Requires OPENAI_API_KEY in the process environment. Does not print prompt/response bodies.
func TestLiveSmoke(t *testing.T) {
	account, err := NewOpenAIAccountFromEnv()
	if err != nil {
		t.Fatalf("account: %v", err)
	}

	ctx := context.Background()
	client, err := newClient(ctx, account)
	if err != nil {
		t.Fatalf("init: %v", err)
	}
	t.Cleanup(func() { shutdownClient(client) })

	requestID := "live-" + uuid.NewString()
	start := time.Now()
	meta, err := runChatSmoke(ctx, client, requestID)
	if err != nil {
		t.Fatalf("chat smoke: %v", err)
	}
	if !meta.OK || meta.ContentChars == 0 {
		t.Fatalf("unexpected meta: %+v", meta)
	}
	t.Logf("%s wall_ms=%d", FormatSmokeMeta(meta), time.Since(start).Milliseconds())
}
