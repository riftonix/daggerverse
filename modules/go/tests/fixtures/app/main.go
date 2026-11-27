package main

import _ "embed"

//go:embed message.txt
var message string

func main() {
	print(message)
}
