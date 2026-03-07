import { useState, useEffect } from 'react'
import {
  View,
  Text,
  Image,
  ScrollView,
  ActivityIndicator,
  StyleSheet,
  Dimensions,
  TouchableOpacity,
  Modal,
  StatusBar,
} from 'react-native'

const API_BASE = "https://apod-production-9b08.up.railway.app"
const { width, height } = Dimensions.get('window')

export default function App() {
  const [imageData, setImageData] = useState(null)
  const [wordData, setWordData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [modalVisible, setModalVisible] = useState(false)

  useEffect(() => {
    const fetchToday = async () => {
      try {
        const [imgResponse, wordResponse] = await Promise.all([
          fetch(`${API_BASE}/image/today`),
          fetch(`${API_BASE}/word/today`),
        ])

        const img = await imgResponse.json()
        const word = await wordResponse.json()

        setImageData(img)
        setWordData(word)
      } catch (e) {
        setError("Could not connect to server.")
      } finally {
        setLoading(false)
      }
    }

    fetchToday()
  }, [])

  if (loading) {
    return (
      <View style={styles.centered}>
        <ActivityIndicator size="large" color="#e8c97e" />
        <Text style={styles.loadingText}>Loading today's universe...</Text>
      </View>
    )
  }

  if (error) {
    return (
      <View style={styles.centered}>
        <Text style={styles.errorText}>{error}</Text>
      </View>
    )
  }

  return (
    <View style={styles.wrapper}>
      <StatusBar barStyle="light-content" backgroundColor="#0a0a0f" />
      {/* fullscreen image modal */}
      <Modal
        visible={modalVisible}
        transparent={true}
        animationType="fade"
        onRequestClose={() => setModalVisible(false)}
      >
        <View style={styles.modalContainer}>
          <StatusBar hidden={true} />
          <Image
            source={{ uri: imageData?.url }}
            style={styles.modalImage}
            resizeMode="contain"   
          />
          <TouchableOpacity
            style={styles.closeButton}
            onPress={() => setModalVisible(false)}
          >
            <Text style={styles.closeText}>✕</Text>
          </TouchableOpacity>
        </View>
      </Modal>

      <ScrollView
        contentContainerStyle={styles.container}
        showsVerticalScrollIndicator={false}
      >
        {/* date */}
        <Text style={styles.date}>{imageData?.date}</Text>

        {/* tappable image */}
        {imageData?.media_type === 'image' ? (
          <TouchableOpacity onPress={() => setModalVisible(true)}>
              <Image
                  source={{ uri: imageData?.url }}
                  style={styles.image}
                  resizeMode="cover"
              />
              <Text style={styles.tapHint}>tap to expand</Text>
          </TouchableOpacity>
      ) : (
          <View style={styles.videoContainer}>
              <Text style={styles.videoNotice}>🎬 Today's APOD is a video</Text>
              <Text style={styles.videoUrl}>{imageData?.url}</Text>
          </View>
      )}

        {/* image title */}
        <Text style={styles.imageTitle}>{imageData?.title}</Text>

        {/* explanation */}
        <Text style={styles.explanation}>{imageData?.explanation}</Text>

        {/* divider */}
        <View style={styles.divider} />

        {/* word of the day */}
        <Text style={styles.wordLabel}>WORD OF THE DAY</Text>
        <Text style={styles.word}>{wordData?.word}</Text>
        <Text style={styles.definition}>{wordData?.definition}</Text>

        <View style={styles.bottomPadding} />
      </ScrollView>
    </View>
  )
}

const styles = StyleSheet.create({
  wrapper: {
    flex: 1,
    backgroundColor: '#0a0a0f',
  },
  container: {
    paddingHorizontal: 20,
    paddingVertical: 50,
  },
  centered: {
    flex: 1,
    backgroundColor: '#0a0a0f',
    justifyContent: 'center',
    alignItems: 'center',
  },
  loadingText: {
    color: '#e8c97e',
    marginTop: 16,
    fontSize: 14,
    letterSpacing: 1,
  },
  errorText: {
    color: '#ff6b6b',
    fontSize: 16,
    textAlign: 'center',
    paddingHorizontal: 40,
  },
  date: {
    color: '#e8c97e',
    fontSize: 12,
    letterSpacing: 3,
    marginBottom: 16,
    textTransform: 'uppercase',
  },
  image: {
    width: width - 40,
    height: (width - 40) * 0.65,
    borderRadius: 8,
    marginBottom: 6,
  },
  tapHint: {
    color: '#444466',
    fontSize: 11,
    letterSpacing: 1,
    marginBottom: 16,
    textAlign: 'right',
  },
  imageTitle: {
    color: '#ffffff',
    fontSize: 22,
    fontWeight: '700',
    marginBottom: 12,
    lineHeight: 30,
  },
  explanation: {
    color: '#8888aa',
    fontSize: 14,
    lineHeight: 22,
    marginBottom: 32,
  },
  divider: {
    height: 1,
    backgroundColor: '#222233',
    marginBottom: 32,
  },
  wordLabel: {
    color: '#e8c97e',
    fontSize: 11,
    letterSpacing: 3,
    marginBottom: 8,
  },
  word: {
    color: '#ffffff',
    fontSize: 32,
    fontWeight: '700',
    marginBottom: 12,
  },
  definition: {
    color: '#8888aa',
    fontSize: 15,
    lineHeight: 24,
  },
  bottomPadding: {
    height: 60,
  },
  modalContainer: {
    flex: 1,
    backgroundColor: '#000000',
    justifyContent: 'center',
    alignItems: 'center',
  },
  modalImage: {
    width: width,
    height: height,
  },
  closeButton: {
    position: 'absolute',
    top: 50,
    right: 20,
    backgroundColor: 'rgba(0,0,0,0.6)',
    borderRadius: 20,
    width: 40,
    height: 40,
    justifyContent: 'center',
    alignItems: 'center',
  },
  closeText: {
    color: '#ffffff',
    fontSize: 16,
  },
  videoContainer: {
    width: width - 40,
    height: (width - 40) * 0.65,
    borderRadius: 8,
    backgroundColor: '#111122',
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 16,
  },
  videoNotice: {
      color: '#e8c97e',
      fontSize: 16,
      marginBottom: 8,
  },
  videoUrl: {
      color: '#444466',
      fontSize: 11,
      textAlign: 'center',
      paddingHorizontal: 20,
  },
})