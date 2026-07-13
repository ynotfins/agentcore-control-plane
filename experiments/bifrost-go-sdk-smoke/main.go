package main

import (
	"context"
	"fmt"
	"log"
	"os"
	"time"

	"github.com/google/uuid"
)

func main() {
	log.SetFlags(0)
	log.SetOutput(os.Stdout)

	if err := run(context.Background()); err != nil {
		log.Printf("status=error message=%q", err.Error())
		os.Exit(1)
	}
}

func run(parent context.Context) error {
	account, err := NewOpenAIAccountFromEnv()
	if err != nil {
		return err
	}

	client, err := newClient(parent, account)
	if err != nil {
		return err
	}
	defer shutdownClient(client)

	requestID := "smoke-" + uuid.NewString()
	start := time.Now()
	meta, err := runChatSmoke(parent, client, requestID)
	if err != nil {
		return fmt.Errorf("chat smoke: %w", err)
	}
	log.Printf("%s wall_ms=%d", FormatSmokeMeta(meta), time.Since(start).Milliseconds())

	streamID := "stream-" + uuid.NewString()
	streamStart := time.Now()
	streamMeta, err := runStreamSmoke(parent, client, streamID)
	if err != nil {
		return fmt.Errorf("stream smoke: %w", err)
	}
	log.Printf("%s wall_ms=%d mode=stream", FormatSmokeMeta(streamMeta), time.Since(streamStart).Milliseconds())

	log.Printf("status=complete note=%q", "Go SDK model-routing smoke only; not the Bifrost MCP Gateway")
	return nil
}
