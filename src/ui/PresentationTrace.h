#pragma once

// Opt-in, diagnostic-only presentation observer. Never call from real-time audio
// callbacks: this bounded producer may allocate and lock. Drain from GSE/main.
#include <atomic>
#include <cstdint>
#include <mutex>
#include <string>
#include <vector>

namespace ui::presentation {

inline std::string Quote( const std::string& value ) {
	std::string result = "\"";
	const char* hex = "0123456789abcdef";
	for ( const unsigned char c : value ) {
		if ( c == '"' || c == '\\' ) { result += '\\'; result += c; }
		else if ( c < 32 ) { result += "\\u00"; result += hex[c >> 4]; result += hex[c & 15]; }
		else { result += c; }
	}
	return result + '"';
}

class Observer {
public:
	static constexpr size_t MAX_EVENTS = 65536;
	static constexpr size_t MAX_BYTES = 16 * 1024 * 1024;
	static constexpr size_t MAX_PAYLOAD_BYTES = 16384;

	bool Enabled() const { return m_enabled.load( std::memory_order_relaxed ); }
	void Start() {
		std::lock_guard< std::mutex > lock( m_mutex );
		m_events.clear(); m_bytes = 0; m_dropped = 0; m_seq = 0; m_seal_requested.store( false );
		m_enabled.store( true, std::memory_order_relaxed );
	}
	void Stop() { m_enabled.store( false, std::memory_order_relaxed ); }
	void RequestSeal() { m_seal_requested.store( true ); }
	bool SealRequested() const { return m_seal_requested.load(); }
	void Record( const std::string& kind, const std::string& target, const std::string& data = "{}" ) {
		if ( !Enabled() ) { return; }
		std::lock_guard< std::mutex > lock( m_mutex );
		if ( !Enabled() ) { return; }
		const auto seq = ++m_seq;
		if ( m_events.size() >= MAX_EVENTS || data.size() > MAX_PAYLOAD_BYTES || m_bytes + data.size() + kind.size() + target.size() + 100 > MAX_BYTES ) {
			++m_dropped;
			return;
		}
		auto record = "{\"seq\":" + std::to_string( seq ) + ",\"kind\":" + Quote( kind ) + ",\"target\":" + Quote( target ) + ",\"data\":" + data + "}";
		m_bytes += record.size();
		m_events.push_back( std::move( record ) );
	}
	std::string Drain( const bool seal = false ) {
		std::lock_guard< std::mutex > lock( m_mutex );
		std::string result = "{\"enabled\":" + std::string( Enabled() ? "true" : "false" ) + ",\"dropped\":" + std::to_string( m_dropped ) + ",\"events\":[";
		bool first = true;
		for ( const auto& event : m_events ) { if ( !first ) { result += ','; } first = false; result += event; }
		m_events.clear(); m_bytes = 0;
		if ( seal ) { m_enabled.store( false, std::memory_order_relaxed ); }
		return result + "]}";
	}
private:
	std::atomic< bool > m_enabled{ false };
	std::atomic< bool > m_seal_requested{ false };
	std::mutex m_mutex;
	std::vector< std::string > m_events;
	size_t m_bytes = 0;
	uint64_t m_seq = 0, m_dropped = 0;
};

// Rewind/Play can be reached by looping playback inside GetNextBuffer. The
// callback guard prevents any diagnostic allocation/locking on that path.
inline thread_local bool in_audio_callback = false;
class AudioCallbackScope {
public:
	AudioCallbackScope() : previous( in_audio_callback ) { in_audio_callback = true; }
	~AudioCallbackScope() { in_audio_callback = previous; }
private:
	bool previous;
};

inline Observer& Get() { static Observer observer; return observer; }
inline bool CanRecordControl() { return !in_audio_callback && Get().Enabled(); }
inline std::string Node( const uint64_t id ) { return "n" + std::to_string( id ); }
inline std::string Playback( const uint64_t id ) { return "m" + std::to_string( id ); }
inline uint64_t NextPlayback() { static std::atomic< uint64_t > id{ 0 }; return ++id; }
inline void Event( const std::string& kind, const std::string& target, const std::string& data = "{}" ) { Get().Record( kind, target, data ); }

}

// Arguments are evaluated only when tracing is enabled.
#define PRESENTATION_EVENT( ... ) do { if ( ::ui::presentation::Get().Enabled() ) { ::ui::presentation::Event( __VA_ARGS__ ); } } while ( false )
