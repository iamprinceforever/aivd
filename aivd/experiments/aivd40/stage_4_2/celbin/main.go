package main

import (
	"encoding/json"
	"fmt"
	"os"

	"github.com/google/cel-go/cel"
	"github.com/google/cel-go/common/types"
	"github.com/google/cel-go/common/types/ref"
	"github.com/google/cel-go/common/types/traits"
)

// Expressions that belong to the frozen sample. This process refuses them
// before compile, so an implementation test cannot measure that sample.
var frozen = map[string]bool{
	"(input + input) + input": true,
	"input":                   true,
	"input + (input + input)": true,
	"input + input":           true,
}

type request struct {
	Expression string `json:"expression"`
	Input      string `json:"input"`
}

func main() {
	var req request
	if err := json.NewDecoder(os.Stdin).Decode(&req); err != nil {
		write(map[string]any{"ok": false, "kind": "invalid"})
		os.Exit(0)
	}
	if frozen[req.Expression] && os.Getenv("AIVD_F2_AUTHORIZED") != "1" {
		write(map[string]any{"ok": false, "kind": "blocked"})
		os.Exit(0)
	}
	env, err := cel.NewEnv(cel.Variable("input", cel.StringType))
	if err != nil {
		write(map[string]any{"ok": false, "kind": "eval"})
		return
	}
	ast, iss := env.Compile(req.Expression)
	if iss != nil && iss.Err() != nil {
		write(map[string]any{"ok": false, "kind": "eval"})
		return
	}
	prg, err := env.Program(ast)
	if err != nil {
		write(map[string]any{"ok": false, "kind": "eval"})
		return
	}
	out, _, err := prg.Eval(map[string]any{"input": req.Input})
	if err != nil {
		write(map[string]any{"ok": false, "kind": "eval"})
		return
	}
	canon, ok := canonical(out)
	if !ok {
		write(map[string]any{"ok": false, "kind": "unsupported"})
		return
	}
	write(map[string]any{"ok": true, "canonical": canon})
}

func canonical(v ref.Val) (any, bool) {
	switch v.Type() {
	case types.StringType:
		s, ok := v.Value().(string)
		if !ok {
			return nil, false
		}
		return map[string]any{"t": "string", "v": s}, true
	case types.IntType:
		n, ok := v.Value().(int64)
		if !ok {
			return nil, false
		}
		return map[string]any{"t": "int", "v": fmt.Sprintf("%d", n)}, true
	case types.BoolType:
		b, ok := v.Value().(bool)
		if !ok {
			return nil, false
		}
		word := "false"
		if b {
			word = "true"
		}
		return map[string]any{"t": "bool", "v": word}, true
	case types.ListType:
		l, ok := v.(traits.Lister)
		if !ok {
			return nil, false
		}
		n, ok := l.Size().Value().(int64)
		if !ok {
			return nil, false
		}
		items := make([]any, 0, n)
		for i := int64(0); i < n; i++ {
			item, ok := canonical(l.Get(types.Int(i)))
			if !ok {
				return nil, false
			}
			items = append(items, item)
		}
		return map[string]any{"t": "list", "v": items}, true
	default:
		return nil, false
	}
}

func write(v map[string]any) {
	enc := json.NewEncoder(os.Stdout)
	enc.SetEscapeHTML(false)
	_ = enc.Encode(v)
}
